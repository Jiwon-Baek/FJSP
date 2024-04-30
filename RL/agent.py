import os, json
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np

torch.manual_seed(42)
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class PPO(nn.Module):
    def __init__(self, cfg, state_dim, action_dim, lr=None, optimizer_name=None, eps_clip=None, K_epoch=None):
        super(PPO, self).__init__()
        self.gamma = cfg.gamma
        self.lmbda = cfg.lmbda
        self.eps_clip = cfg.eps_clip if eps_clip is None else eps_clip
        self.K_epoch = cfg.K_epoch if K_epoch is None else K_epoch
        self.lr = cfg.lr if lr is None else lr
        self.optim = cfg.optim if optimizer_name is None else optimizer_name
        self.data = []

        self.fc1 = nn.Linear(state_dim, 512)
        self.fc2 = nn.Linear(512, 512)
        self.fc3 = nn.Linear(512, 256)
        self.fc_pi = nn.Linear(256, action_dim)
        self.fc_v = nn.Linear(256, 1)
        if cfg.optim == "Adam":
            self.optimizer = optim.Adam(self.parameters(), lr=self.lr)
        elif cfg.optim == "AdaHessian":
            self.optimizer = optim.Adam(self.parameters(), lr=self.lr)
            # self.optimizer = AdaHessian(self.parameters(), lr=self.lr)

    # define policy iteration network
    def pi(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc_pi(x)
        return x

    # define value network
    def v(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        v = self.fc_v(x)
        return v

    def put_data(self, transition):
        self.data.append(transition)

    def make_batch(self):
        s_lst, a_lst, r_lst, s_prime_lst, prob_a_lst, done_lst = [], [], [], [], [], []
        for transition in self.data:
            s, a, r, s_prime, prob_a, done = transition

            s_lst.append(s)
            a_lst.append([a])
            r_lst.append([r])
            s_prime_lst.append(s_prime)
            prob_a_lst.append([prob_a])
            done_mask = 0 if done else 1
            done_lst.append([done_mask])

        # self.data에 있는 transition들을 list 변수에 담고 tensor화
        # 데이터를 배치로 변화시키는 과정
        s_lst = np.array(s_lst)
        a_lst = np.array(a_lst)
        r_lst = np.array(r_lst)
        s_prime_lst = np.array(s_prime_lst)
        prob_a_lst = np.array(prob_a_lst)
        done_lst = np.array(done_lst)

        s, a, r, s_prime, prob_a, done = torch.tensor(s_lst, dtype=torch.float).to(device), torch.tensor(a_lst, dtype=torch.int64).to(device), \
                                         torch.tensor(r_lst, dtype=torch.float).to(device), torch.tensor(s_prime_lst, dtype=torch.float).to(device), \
                                         torch.tensor(prob_a_lst).to(device), torch.tensor(done_lst, dtype=torch.float).to(device)

        self.data = []
        return s, a, r, s_prime, prob_a, done

    def train_net(self):
        s, a, r, s_prime, prob_a, done = self.make_batch()

        for i in range(self.K_epoch):
            td_target = r + self.gamma * self.v(s_prime) * done
            delta = td_target - self.v(s)
            delta = delta.cpu().detach().numpy()

            advantage_lst = []
            advantage = 0.0
            for delta_t in delta[::-1]:
                advantage = self.gamma * self.lmbda * advantage + delta_t[0]
                advantage_lst.append([advantage])
            advantage_lst.reverse()
            advantage = torch.tensor(advantage_lst, dtype=torch.float).to(device)

            logit = self.pi(s)
            pi = torch.softmax(logit, dim=-1)
            pi_a = pi.gather(1, a)
            ratio = torch.exp(torch.log(pi_a) - torch.log(prob_a))  # a/b == exp(log(a)-log(b))

            surr1 = ratio * advantage
            surr2 = torch.clamp(ratio, 1 - self.eps_clip, 1 + self.eps_clip) * advantage
            loss = -torch.min(surr1, surr2) + 0.5 * F.smooth_l1_loss(self.v(s), td_target.detach())

            self.optimizer.zero_grad()
            if self.optim == "Adam":
                loss.mean().backward()
            elif self.optim == "AdaHessian":
                loss.mean().backward(create_graph=True)
            self.optimizer.step()

    def save(self, episode, file_dir):
        torch.save({"episode": episode,
                    "model_state_dict": self.state_dict(),
                    "optimizer_state_dict": self.optimizer.state_dict()},
                   file_dir + "episode-%d.pt" % episode)

