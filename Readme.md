# 파일 실행 순서
1. data.py에 데이터 연결
2. config.py에서 여러가지 시뮬레이션 관련 변수 설정
3. test_main.py 나 main.py 실행

# Executable Files

1. main.py
2. test_main.py
3. GA_V2.py

# Module Descriptions
- environment
  - monitor.py
  - part.py
  - process.py
  - resource.py
  - Sink.py
  - Source.py
- postprocessing
  - PostProcessing.py
- test
  - test_main.py
- visualization
  - Gantt.py
  - GUI.py
  
- main.py
- config.py : 시뮬레이션 관련 세팅
- data.py : Job data ( + 필요할 경우 검증용 solution까지) 입력
