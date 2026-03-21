-- 007_pricing_module.sql
-- 비딩 가격 산정 및 전략적 의사결정 모듈
-- market_price_data 확장 + 시뮬레이션 이력 + 예측 정확도 추적

-- ══════════════════════════════════════
-- 1. market_price_data 컬럼 확장
-- ══════════════════════════════════════

ALTER TABLE market_price_data
  ADD COLUMN IF NOT EXISTS estimated_price BIGINT,
  ADD COLUMN IF NOT EXISTS winner_name VARCHAR(200),
  ADD COLUMN IF NOT EXISTS budget_tier VARCHAR(20),
  ADD COLUMN IF NOT EXISTS tech_score DECIMAL(5,2),
  ADD COLUMN IF NOT EXISTS price_score DECIMAL(5,2),
  ADD COLUMN IF NOT EXISTS evaluation_method VARCHAR(50);

-- budget_tier 자동 계산 트리거
CREATE OR REPLACE FUNCTION compute_budget_tier()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.budget IS NOT NULL THEN
    IF NEW.budget < 500000000 THEN
      NEW.budget_tier := '<500M';
    ELSIF NEW.budget < 1000000000 THEN
      NEW.budget_tier := '500M-1B';
    ELSE
      NEW.budget_tier := '>1B';
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_budget_tier ON market_price_data;
CREATE TRIGGER trg_budget_tier
  BEFORE INSERT OR UPDATE OF budget ON market_price_data
  FOR EACH ROW
  EXECUTE FUNCTION compute_budget_tier();

-- 기존 행에 budget_tier 채우기
UPDATE market_price_data SET budget_tier = CASE
  WHEN budget < 500000000 THEN '<500M'
  WHEN budget < 1000000000 THEN '500M-1B'
  ELSE '>1B'
END WHERE budget IS NOT NULL AND budget_tier IS NULL;


-- ══════════════════════════════════════
-- 2. pricing_simulations 테이블
-- ══════════════════════════════════════

CREATE TABLE IF NOT EXISTS pricing_simulations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id     UUID REFERENCES proposals(id) ON DELETE SET NULL,
  org_id          UUID NOT NULL,
  created_by      UUID,
  -- 입력
  params          JSONB NOT NULL,
  -- 결과
  result          JSONB NOT NULL,
  -- 사용자 선택
  selected_scenario VARCHAR(50),
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pricing_sim_org ON pricing_simulations(org_id);
CREATE INDEX IF NOT EXISTS idx_pricing_sim_proposal ON pricing_simulations(proposal_id);
CREATE INDEX IF NOT EXISTS idx_pricing_sim_created ON pricing_simulations(created_at DESC);


-- ══════════════════════════════════════
-- 3. pricing_predictions 테이블
-- ══════════════════════════════════════

CREATE TABLE IF NOT EXISTS pricing_predictions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_id   UUID REFERENCES pricing_simulations(id) ON DELETE CASCADE,
  proposal_id     UUID REFERENCES proposals(id) ON DELETE SET NULL,
  predicted_ratio DECIMAL(5,4),
  predicted_win_prob DECIMAL(5,4),
  actual_ratio    DECIMAL(5,4),
  actual_result   TEXT,  -- won | lost | void
  prediction_error DECIMAL(5,4),
  created_at      TIMESTAMPTZ DEFAULT now(),
  resolved_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pricing_pred_proposal ON pricing_predictions(proposal_id);
CREATE INDEX IF NOT EXISTS idx_pricing_pred_sim ON pricing_predictions(simulation_id);


-- ══════════════════════════════════════
-- 4. market_price_data 도메인 + 방식 인덱스
-- ══════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_mpd_domain_method
  ON market_price_data(domain, evaluation_method);
CREATE INDEX IF NOT EXISTS idx_mpd_budget_tier
  ON market_price_data(budget_tier);
