import os
import torch
import json
import math

from cfg_local import Configure
from RL.agent import *
from environment.FJSP import *

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

if __name__ == "__main__":
    cfg = Configure()
    # if cfg.use_vessl:
    #     vessl.init(organization="sun-eng-dgx", project="Final-General-PMSP", hp=cfg)

    optim = "Adam"
    learning_rate = 0.005 if not cfg.use_vessl else cfg.lr
    K_epoch = 1 if not cfg.use_vessl else cfg.K_epoch
    T_horizon = "entire" if not cfg.use_vessl else cfg.T_horizon
    num_episode = 10000
    num_job = cfg.num_job
    num_m = cfg.num_machine
    data = [0., 0., 0.]

    env = FJSP(cfg, data)
    agent = PPO(cfg, env.state_dim, env.action_dim, optimizer_name=optim, K_epoch=K_epoch).to(device)

    if cfg.load_model:
        checkpoint = torch.load('./trained_model/episode-30000.pt')
        start_episode = checkpoint['episode'] + 1
        pass
    else:
        start_episode = 1

    for episode in range(start_episode, start_episode + num_episode):
        state = env.reset()
        done = False

        while not done:
            pass
            if done:
                pass
        agent.train_net()

        if episode % 100 == 0 or episode == 1:
            pass
