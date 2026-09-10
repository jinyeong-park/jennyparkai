# 파일 구성

총 3개의 독립된 파일로 구성됩니다.
실무 환경에서는 마케팅 매체 데이터, 웹로그 데이터, 백엔드 결제 데이터가 각각 다른 시스템에서 수집되어 들어오기 때문에, 이를 3개의 원천 테이블(Raw Files)로 나누어 생성한 뒤 SQL로 통합(Join & Aggregate)하고 가공하도록 설계했습니다.

### **📂 3개 파일이 상징하는 현업 데이터 시스템**

| 생성할 파일명                | 실제 현업 데이터 출처                         | 데이터의 성격 및 특징                                                  |
| :--------------------------- | :-------------------------------------------- | :--------------------------------------------------------------------- |
| **raw_ad_spend.csv**         | **MAPI (Meta, Google Ads, TikTok API)**       | 매체별 지출 비용(Spend)과 매체 자사가 주장하는 과장된 성과 테이블      |
| **raw_user_touchpoints.csv** | **CDP / Web Clickstream (Segment, GA4)**      | 유저가 결제하기 전 광고/검색으로 접속한 모든 유저 여정 타임스탬프 로그 |
| **raw_conversions.csv**      | **Backend DB / E-commerce (Stripe, Shopify)** | 실제로 돈이 결제되어 발생한 진짜 매출 및 주문 정보                     |

### **💡 Realistic Environment(실제 마케팅 분석 환경)를 100% 재현하는 4단계 프로세스**

포트폴리오의 깊이를 극대화하고, 면접관이 \*"이 친구는 진짜 현업 파이프라인 프로세스를 타봤구나"\*라고 느끼게 만들려면 **아래 4단계 흐름**으로 작업을 진행해야 합니다.

Plaintext  
\[1단계: Data Generation\] \[2단계: SQL Data Warehouse\] \[3단계: Analytics Modeling\] \[4단계: Executive Dashboard\]  
 Raw CSV 파일 3개 생성 ──\> PostgreSQL / DuckDB 적재 ──\> Attribution & Geo Test SQL ──\> Streamlit / Tableau 시각화  
(Python Faker/Numpy) (UTM 정제 & Deduplication) (First/Last/Time-Decay) (C-Level Decision App)

#### **1단계: 원천 데이터 생성 (Data Generation)**

- 위에서 작성한 프롬프트로 3개의 CSV 파일을 생성하여 data/raw/ 폴더에 적재합니다.
- 일부러 들어간 **대소문자 불일치, duplicate log, null값**이 존재하는 상태입니다.

#### **2단계: 데이터웨어하우스 적재 및 정제 (Cleaning & Staging \- SQL)**

- CSV 파일 3개를 **PostgreSQL**, **DuckDB**, 또는 **Snowflake**에 테이블로 로딩합니다.
- 01_data_cleaning.sql 쿼리를 짜서 다음과 같이 가공합니다:
  - LOWER(utm_source)로 Meta, meta, META를 하나의 meta로 통합
  - 1초 이내 동일 유저의 중복 클릭 이벤트 제거 (ROW_NUMBER() 활용)
  - COALESCE()를 활용한 missing UTM 처리

#### **3단계: 기여도 모델링 및 데이터 통합 (Multi-Touch Attribution \- SQL)**

- 유저 ID 기준으로 touchpoints 테이블과 conversions 테이블을 JOIN합니다.
- SQL Window Function(FIRST_VALUE, LAST_VALUE, LAG)을 사용해 유저별 터치포인트 순서를 1, 2, 3으로 나열합니다.
- **First-Touch, Last-Touch, Time-Decay** 기여도에 따라 각 채널에 매출 $를 분배(Attribute)합니다.

#### **4단계: 매체 리포트와 실제 증분 매출 비교 분석 (Incrementality \- Python & App)**

- raw_ad_spend 테이블의 비용 데이터와 3단계의 귀인 매출 데이터를 결합하여 **채널별 진짜 ROAS**를 구합니다.
- 플랫폼이 자체 리포팅한 성과와 SQL로 정제한 성과의 차이(Bias)를 계산하여 대시보드에 시각화합니다.


