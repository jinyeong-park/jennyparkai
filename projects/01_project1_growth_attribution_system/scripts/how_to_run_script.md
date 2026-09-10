📂 실행 방법
프로젝트 폴더 터미널에서 아래 명령어로 의존성 패키지를 설치합니다:
Bash
pip install pandas numpy

위의 코드를 scripts/generate_synthetic_data.py로 복사해 저장합니다.
scripts 보다 한 단계 상위 폴더로 가서
터미널에서 스크립트를 실행합니다:
Bash
python scripts/generate_synthetic_data.py

실행이 끝나면 data/raw/ 폴더 아래에 3개의 CSV 파일이 생성되며, 다음 단계인 SQL 정제 및 데이터 적재(01_data_cleaning.sql) 단계로 바로 진입하실 수 있습니다!
