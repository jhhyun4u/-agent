"use client";

/**
 * 랜딩페이지 — 비인증 사용자에게 표시
 * 로그인된 사용자는 /dashboard로 자동 리다이렉트
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

interface LandingStats {
  daily_bids_monitored: number;
  screening_accuracy_pct: number;
  hours_saved: number;
  reference_projects: number;
  today_new_bids: number;
  today_recommended: number;
  deadline_urgent: number;
  monthly_proposals: number;
}

export default function LandingPage() {
  const router = useRouter();
  const [stats, setStats] = useState<LandingStats | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        router.replace("/dashboard");
      } else {
        setChecking(false);
      }
    });
  }, [router]);

  useEffect(() => {
    if (checking) return;
    fetch(`${API_BASE}/public/stats`)
      .then((r) => r.json())
      .then((json) => setStats(json.data))
      .catch(() => {});
  }, [checking]);

  if (checking) return null;

  const s = stats;

  return (
    <>
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=DM+Serif+Display&display=swap');

        .landing * { box-sizing: border-box; margin: 0; padding: 0; }
        .landing { font-family: 'Noto Sans KR', sans-serif; background: #F5F2ED; color: #1A2332; line-height: 1.7; }

        /* NAV */
        .l-nav {
          background: #0D1B2A;
          border-bottom: 1px solid rgba(201,168,76,0.2);
          height: 62px;
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 48px;
          position: sticky; top: 0; z-index: 100;
        }
        .l-nav-brand { display: flex; align-items: center; gap: 10px; }
        .l-nav-icon {
          width: 34px; height: 34px; background: #C9A84C;
          border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        }
        .l-nav-icon span {
          font-family: 'DM Serif Display', serif;
          font-size: 12.5px; font-weight: 700; color: #0D1B2A; letter-spacing: -0.5px;
        }
        .l-nav-name { font-family: 'DM Serif Display', serif; color: #fff; font-size: 17px; line-height: 1.1; }
        .l-nav-name em { color: #E8C87A; display: block; font-style: normal; }
        .l-nav-badge {
          background: rgba(201,168,76,0.15); border: 1px solid rgba(201,168,76,0.28);
          color: #C9A84C; font-size: 10px; font-weight: 600; padding: 2px 9px; border-radius: 20px;
        }
        .l-nav-right { display: flex; align-items: center; gap: 28px; }
        .l-nav-link { color: rgba(255,255,255,0.55); font-size: 13px; text-decoration: none; }
        .l-nav-link:hover { color: #E8C87A; }
        .btn-nav {
          background: #C9A84C; color: #0D1B2A;
          border: none; padding: 9px 24px; border-radius: 7px;
          font-size: 13.5px; font-weight: 700; cursor: pointer;
          font-family: 'Noto Sans KR', sans-serif;
          box-shadow: 0 2px 14px rgba(201,168,76,0.5);
        }
        .btn-nav:hover { background: #E8C87A; }

        /* HERO */
        .l-hero-wrap { background: #0D1B2A; }
        .l-hero {
          max-width: 1160px; margin: 0 auto;
          padding: 80px 48px 88px;
          display: flex; align-items: center; gap: 60px;
          position: relative; overflow: hidden;
        }
        .l-hero::before {
          content: ''; position: absolute; inset: 0;
          background-image: radial-gradient(circle, rgba(201,168,76,0.13) 1px, transparent 1px);
          background-size: 32px 32px; pointer-events: none;
        }
        .l-hero-copy { flex: 1; position: relative; z-index: 1; }
        .l-hero-eyebrow {
          display: inline-flex; align-items: center; gap: 7px;
          background: rgba(201,168,76,0.12); border: 1px solid rgba(201,168,76,0.3);
          color: #E8C87A; padding: 5px 14px; border-radius: 20px;
          font-size: 11.5px; font-weight: 600; margin-bottom: 22px;
        }
        .l-live-dot { width: 6px; height: 6px; background: #2ECC71; border-radius: 50%; animation: l-blink 2s infinite; }
        @keyframes l-blink { 0%,100%{opacity:1} 50%{opacity:0.25} }
        .l-hero-copy h1 {
          font-family: 'DM Serif Display', serif;
          font-size: clamp(30px, 3.8vw, 48px);
          color: #fff; line-height: 1.25; letter-spacing: -0.5px; margin-bottom: 20px;
        }
        .l-hero-copy h1 em { color: #E8C87A; font-style: normal; }
        .l-hero-copy p { color: rgba(255,255,255,0.58); font-size: 15px; margin-bottom: 36px; max-width: 460px; line-height: 1.75; }
        .btn-hero {
          background: #C9A84C; color: #0D1B2A;
          border: none; padding: 13px 32px; border-radius: 9px;
          font-size: 15px; font-weight: 700; cursor: pointer;
          font-family: 'Noto Sans KR', sans-serif;
          box-shadow: 0 4px 24px rgba(201,168,76,0.55);
          display: inline-block; text-decoration: none;
        }
        .btn-hero:hover { background: #E8C87A; }

        .l-hero-card {
          width: 280px; flex-shrink: 0; position: relative; z-index: 1;
          background: rgba(255,255,255,0.06); border: 1px solid rgba(201,168,76,0.22);
          border-radius: 14px; padding: 22px 20px;
        }
        .hc-head { color: rgba(255,255,255,0.38); font-size: 10.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 14px; }
        .hc-row { display: flex; justify-content: space-between; align-items: center; padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .hc-row:last-child { border-bottom: none; }
        .hc-lbl { color: rgba(255,255,255,0.48); font-size: 12.5px; }
        .hc-val { font-size: 15px; font-weight: 700; color: #E8C87A; }
        .hc-val-red { font-size: 15px; font-weight: 700; color: #FF8A8A; }
        .hc-val-green { font-size: 15px; font-weight: 700; color: #5EE87A; }

        /* STATS STRIP */
        .l-stats-strip {
          background: #152438;
          border-top: 1px solid rgba(201,168,76,0.12);
          border-bottom: 1px solid rgba(201,168,76,0.12);
          display: flex; justify-content: center; flex-wrap: wrap;
        }
        .l-stat-cell { text-align: center; padding: 22px 48px; border-right: 1px solid rgba(255,255,255,0.05); }
        .l-stat-cell:last-child { border-right: none; }
        .l-stat-num { color: #E8C87A; font-family: 'DM Serif Display', serif; font-size: 26px; }
        .l-stat-lbl { color: rgba(255,255,255,0.38); font-size: 11.5px; margin-top: 3px; }

        /* SECTIONS */
        .l-section { max-width: 1160px; margin: 0 auto; padding: 76px 48px; }
        .l-sec-tag {
          display: inline-block; background: #FBF5E6; color: #7A5012;
          padding: 4px 13px; border-radius: 20px; font-size: 11px; font-weight: 700;
          letter-spacing: 0.4px; text-transform: uppercase; margin-bottom: 12px;
        }
        .l-sec-title { font-family: 'DM Serif Display', serif; font-size: clamp(24px, 2.8vw, 34px); color: #0D1B2A; line-height: 1.3; margin-bottom: 10px; }
        .l-sec-desc { color: #6B7A8D; font-size: 14.5px; max-width: 500px; margin-bottom: 48px; }

        /* FLOW */
        .l-flow-grid { display: grid; grid-template-columns: repeat(4, 1fr); }
        .l-flow-step {
          background: #fff; border: 1px solid rgba(0,0,0,0.07);
          padding: 28px 22px 24px; position: relative; transition: box-shadow 0.2s;
        }
        .l-flow-step + .l-flow-step { border-left: none; }
        .l-flow-step:first-child { border-radius: 12px 0 0 12px; }
        .l-flow-step:last-child { border-radius: 0 12px 12px 0; }
        .l-flow-step:hover { box-shadow: 0 8px 28px rgba(13,27,42,0.1); z-index: 1; }
        .l-step-num { width: 28px; height: 28px; background: #0D1B2A; color: #C9A84C; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; margin-bottom: 14px; }
        .l-step-ico { font-size: 22px; margin-bottom: 10px; }
        .l-step-title { font-weight: 700; font-size: 13.5px; color: #0D1B2A; margin-bottom: 7px; }
        .l-step-desc { font-size: 12.5px; color: #6B7A8D; line-height: 1.65; }
        .l-step-arr { position: absolute; right: -13px; top: 50%; transform: translateY(-50%); width: 24px; height: 24px; background: #C9A84C; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #0D1B2A; font-size: 11px; font-weight: 700; z-index: 2; }

        /* FEATURES */
        .l-features-bg { background: #EEEAE4; }
        .l-feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
        .l-feat-card { background: #fff; border: 1px solid rgba(0,0,0,0.07); border-radius: 12px; padding: 26px 22px; transition: transform 0.2s, box-shadow 0.2s; }
        .l-feat-card:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(13,27,42,0.09); }
        .l-feat-ico { width: 42px; height: 42px; border-radius: 10px; background: #FBF5E6; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 14px; }
        .l-feat-title { font-weight: 700; font-size: 14px; color: #0D1B2A; margin-bottom: 7px; }
        .l-feat-desc { font-size: 12.5px; color: #6B7A8D; line-height: 1.65; }
        .l-feat-pill { display: inline-block; margin-top: 12px; background: rgba(201,168,76,0.1); color: #8A6010; border: 1px solid rgba(201,168,76,0.22); padding: 3px 10px; border-radius: 20px; font-size: 10.5px; font-weight: 600; }

        /* PREVIEW */
        .l-preview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-items: center; }
        .l-preview-copy h3 { font-family: 'DM Serif Display', serif; font-size: 24px; color: #0D1B2A; margin-bottom: 14px; line-height: 1.35; }
        .l-preview-copy p { color: #6B7A8D; font-size: 14px; line-height: 1.75; margin-bottom: 22px; }
        .l-check-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
        .l-check-list li { display: flex; align-items: flex-start; gap: 9px; font-size: 13.5px; color: #1A2332; }
        .l-check-mark { color: #C9A84C; font-weight: 700; flex-shrink: 0; }
        .l-screen-mock { background: #0D1B2A; border-radius: 12px; overflow: hidden; border: 1px solid rgba(201,168,76,0.18); box-shadow: 0 16px 48px rgba(13,27,42,0.2); }
        .l-mock-bar { background: #152438; padding: 9px 14px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(201,168,76,0.1); }
        .l-dot { width: 8px; height: 8px; border-radius: 50%; }
        .l-mock-body { padding: 16px; display: flex; flex-direction: column; gap: 10px; }
        .l-mock-kpis { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
        .l-mk { background: rgba(255,255,255,0.05); border-radius: 7px; padding: 10px 11px; border: 1px solid rgba(201,168,76,0.1); }
        .l-mk-lbl { color: rgba(255,255,255,0.35); font-size: 9px; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }
        .l-mk-val { color: #fff; font-size: 18px; font-weight: 700; }
        .l-mk-sub { color: #C9A84C; font-size: 9px; margin-top: 2px; }
        .l-mock-thead { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 6px; padding: 6px 10px; background: rgba(255,255,255,0.03); border-radius: 6px; }
        .l-mth { color: rgba(255,255,255,0.25); font-size: 9px; text-transform: uppercase; font-weight: 600; }
        .l-mock-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 6px; padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,0.04); align-items: center; }
        .l-mock-row:last-child { border-bottom: none; }
        .l-mr-t { color: rgba(255,255,255,0.78); font-size: 10px; font-weight: 600; }
        .l-mr-s { color: rgba(255,255,255,0.32); font-size: 9px; margin-top: 1px; }
        .l-mr-amt { color: rgba(255,255,255,0.55); font-size: 10px; }
        .l-sc { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
        .l-sc-h { background: rgba(42,157,92,0.2); color: #5EE87A; }
        .l-sc-m { background: rgba(201,168,76,0.2); color: #E8C87A; }

        /* CTA */
        .l-cta-wrap { background: #0D1B2A; }
        .l-cta-inner { max-width: 1160px; margin: 0 auto; padding: 52px 48px; display: flex; align-items: center; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
        .l-cta-copy h3 { font-family: 'DM Serif Display', serif; color: #fff; font-size: 24px; margin-bottom: 6px; }
        .l-cta-copy p { color: rgba(255,255,255,0.45); font-size: 13.5px; }
        .btn-cta {
          background: #C9A84C; color: #0D1B2A;
          border: none; padding: 14px 40px; border-radius: 9px;
          font-size: 15px; font-weight: 700; cursor: pointer;
          font-family: 'Noto Sans KR', sans-serif; white-space: nowrap;
          box-shadow: 0 4px 24px rgba(201,168,76,0.5);
          text-decoration: none; display: inline-block;
        }
        .btn-cta:hover { background: #E8C87A; }

        .l-footer { background: #07111C; padding: 22px 48px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; border-top: 1px solid rgba(201,168,76,0.1); }
        .l-foot-left { color: rgba(255,255,255,0.28); font-size: 12px; }
        .l-foot-right { display: flex; gap: 22px; }
        .l-foot-right a { color: rgba(255,255,255,0.28); font-size: 12px; text-decoration: none; }
        .l-foot-right a:hover { color: #C9A84C; }

        /* RESPONSIVE */
        @media (max-width: 900px) {
          .l-nav { padding: 0 20px; }
          .l-nav-links { display: none; }
          .l-hero { flex-direction: column; padding: 48px 20px 56px; gap: 32px; }
          .l-hero-card { width: 100%; }
          .l-flow-grid { grid-template-columns: 1fr 1fr; gap: 0; }
          .l-flow-step { border-left: 1px solid rgba(0,0,0,0.07) !important; }
          .l-flow-step:first-child { border-radius: 12px 0 0 0; }
          .l-flow-step:nth-child(2) { border-radius: 0 12px 0 0; }
          .l-flow-step:nth-child(3) { border-radius: 0 0 0 12px; }
          .l-flow-step:last-child { border-radius: 0 0 12px 0; }
          .l-step-arr { display: none; }
          .l-feat-grid { grid-template-columns: 1fr 1fr; }
          .l-preview-grid { grid-template-columns: 1fr; }
          .l-section { padding: 48px 20px; }
          .l-stats-strip { flex-wrap: wrap; }
          .l-stat-cell { flex: 1 1 50%; border-right: none; padding: 16px 20px; }
          .l-cta-inner { flex-direction: column; text-align: center; padding: 40px 20px; }
          .l-footer { flex-direction: column; text-align: center; padding: 20px; }
        }
        @media (max-width: 600px) {
          .l-flow-grid { grid-template-columns: 1fr; }
          .l-flow-step { border-radius: 0 !important; border-left: 1px solid rgba(0,0,0,0.07) !important; }
          .l-flow-step:first-child { border-radius: 12px 12px 0 0 !important; }
          .l-flow-step:last-child { border-radius: 0 0 12px 12px !important; }
          .l-feat-grid { grid-template-columns: 1fr; }
          .l-stat-cell { flex: 1 1 100%; }
          .l-mock-kpis { grid-template-columns: 1fr; }
        }
      `}</style>

      <div className="landing">
        {/* NAV */}
        <nav className="l-nav">
          <div className="l-nav-brand">
            <div className="l-nav-icon"><span>TNP</span></div>
            <div className="l-nav-name">Proposal<em>Coworker</em></div>
            <span className="l-nav-badge">TENOPA INTERNAL</span>
          </div>
          <div className="l-nav-right">
            <span className="l-nav-links">
              <a href="#flow" className="l-nav-link">워크플로우</a>
            </span>
            <span className="l-nav-links">
              <a href="#features" className="l-nav-link">기능 안내</a>
            </span>
            <span className="l-nav-links">
              <a href="#preview" className="l-nav-link">화면 미리보기</a>
            </span>
          </div>
        </nav>

        {/* HERO */}
        <div className="l-hero-wrap">
          <div className="l-hero">
            <div className="l-hero-copy">
              <div className="l-hero-eyebrow">
                <div className="l-live-dot" />
                {s ? `오늘 신규 공고 ${s.today_new_bids}건 수집 완료` : "실시간 공고 수집 중..."}
              </div>
              <h1>
                나라장터 공고부터<br />
                <em>제안서 완성</em>까지<br />
                함께하는 AI 동료
              </h1>
              <p>
                TENOPA 임직원 전용 R&D 수주 자동화 플랫폼.
                공고 모니터링, AI 스크리닝, 제안서 초안 생성을 한 번에 처리하세요.
              </p>
              <a href="/login" className="btn-hero">지금 로그인하기 &rarr;</a>
            </div>
            <div className="l-hero-card">
              <div className="hc-head">오늘 현황 &middot; 실시간</div>
              <div className="hc-row">
                <span className="hc-lbl">신규 공고</span>
                <span className="hc-val">{s ? `${s.today_new_bids}건` : "-"}</span>
              </div>
              <div className="hc-row">
                <span className="hc-lbl">AI 추천 공고</span>
                <span className="hc-val">{s ? `${s.today_recommended}건` : "-"}</span>
              </div>
              <div className="hc-row">
                <span className="hc-lbl">마감 임박 D-3</span>
                <span className="hc-val-red">{s ? `${s.deadline_urgent}건` : "-"}</span>
              </div>
              <div className="hc-row">
                <span className="hc-lbl">이번달 제안</span>
                <span className="hc-val-green">{s ? `${s.monthly_proposals}건` : "-"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* STATS STRIP — 실제 데이터 */}
        <div className="l-stats-strip">
          <div className="l-stat-cell">
            <div className="l-stat-num">{s ? s.daily_bids_monitored.toLocaleString() : "-"}</div>
            <div className="l-stat-lbl">누적 모니터링 공고 수</div>
          </div>
          <div className="l-stat-cell">
            <div className="l-stat-num">{s ? `${s.screening_accuracy_pct}%` : "-"}</div>
            <div className="l-stat-lbl">AI 스크리닝 정확도</div>
          </div>
          <div className="l-stat-cell">
            <div className="l-stat-num">{s ? `${s.hours_saved}시간` : "-"}</div>
            <div className="l-stat-lbl">제안서 초안 작성 시간 단축</div>
          </div>
          <div className="l-stat-cell">
            <div className="l-stat-num">{s ? `${s.reference_projects}+` : "-"}</div>
            <div className="l-stat-lbl">학습 레퍼런스 과제 수</div>
          </div>
        </div>

        {/* FLOW */}
        <div id="flow" style={{ background: "#F5F2ED" }}>
          <div className="l-section">
            <div className="l-sec-tag">자동화 워크플로우</div>
            <h2 className="l-sec-title">
              공고 발견부터 제안서 제출까지<br />원스톱 자동화
            </h2>
            <p className="l-sec-desc">
              반복적인 공고 탐색과 제안서 초안 작성을 AI가 대신합니다.
              컨설턴트는 전략과 검토에만 집중하세요.
            </p>
            <div className="l-flow-grid">
              {[
                { num: 1, ico: "\uD83D\uDD0D", title: "공고 자동 수집\u00B7분류", desc: "나라장터 전 부처 공고를 1시간마다 수집. 기술 분야\u00B7금액\u00B7기간 기준으로 자동 태깅합니다." },
                { num: 2, ico: "\uD83E\uDD16", title: "AI 수주 가능성 스코어링", desc: "보유 이력\u00B7인력\u00B7전문 분야와 공고를 매칭해 수주 가능성 점수를 즉시 산정합니다." },
                { num: 3, ico: "\u270D\uFE0F", title: "제안서 초안 자동 생성", desc: "RFP를 자동 파싱해 수행 방법론\u00B7투입 인력\u00B7추진 일정을 공문서 형식으로 즉시 초안 작성합니다." },
                { num: 4, ico: "\uD83D\uDCC8", title: "제출\u00B7성과 관리", desc: "낙찰\u00B7탈락 피드백을 축적해 다음 제안의 승률을 지속적으로 개선합니다." },
              ].map((step, i, arr) => (
                <div className="l-flow-step" key={step.num}>
                  <div className="l-step-num">{step.num}</div>
                  <div className="l-step-ico">{step.ico}</div>
                  <div className="l-step-title">{step.title}</div>
                  <div className="l-step-desc">{step.desc}</div>
                  {i < arr.length - 1 && <div className="l-step-arr">&rarr;</div>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* FEATURES */}
        <div id="features" className="l-features-bg">
          <div className="l-section">
            <div className="l-sec-tag">핵심 기능</div>
            <h2 className="l-sec-title">
              R&D 컨설팅 실무에<br />꼭 맞는 기능들
            </h2>
            <p className="l-sec-desc">
              기획\u00B7정책 연구\u00B7기술사업화 업무에 특화된 6가지 핵심 기능을 제공합니다.
            </p>
            <div className="l-feat-grid">
              {[
                { ico: "\uD83D\uDCE1", title: "실시간 공고 알림", desc: "키워드\u00B7부처\u00B7금액 조건으로 맞춤 알림 설정. 마감 D-7\u00B7D-3\u00B7D-1 자동 리마인더를 Teams\u00B7이메일로 수신합니다.", pill: "모니터링" },
                { ico: "\uD83D\uDCCA", title: "AI 수주 가능성 스코어", desc: "유사 수행 이력, 요구 자격, 경쟁 강도를 종합 분석. 70점 이상 공고만 집중해 리소스를 최적화합니다.", pill: "AI 분석" },
                { ico: "\u270D\uFE0F", title: "제안서 AI 초안 생성", desc: "공고 RFP를 파싱해 목차\u00B7수행 방법\u00B7추진 일정을 포함한 한국어 공문서 초안을 즉시 생성합니다.", pill: "생성형 AI" },
                { ico: "\uD83D\uDCDA", title: "과제 레퍼런스 라이브러리", desc: "수행 과제의 제안서\u00B7결과보고서를 RAG 기반으로 검색해 유사 사례를 즉시 참조합니다.", pill: "RAG 검색" },
                { ico: "\uD83D\uDC65", title: "팀 협업 & 버전 관리", desc: "제안서 버전 관리, 코멘트 기능, 결재 라인 관리로 팀 전체가 효율적으로 협력합니다.", pill: "협업" },
                { ico: "\uD83D\uDCC8", title: "수주 성과 애널리틱스", desc: "부처별\u00B7분야별 수주율, 평균 제안 금액, 경쟁사 동향을 시각화해 전략 수립에 활용합니다.", pill: "애널리틱스" },
              ].map((f) => (
                <div className="l-feat-card" key={f.title}>
                  <div className="l-feat-ico">{f.ico}</div>
                  <div className="l-feat-title">{f.title}</div>
                  <div className="l-feat-desc">{f.desc}</div>
                  <span className="l-feat-pill">{f.pill}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* PREVIEW */}
        <div id="preview" style={{ background: "#F5F2ED" }}>
          <div className="l-section">
            <div className="l-sec-tag">화면 미리보기</div>
            <h2 className="l-sec-title">
              한눈에 보이는<br />수주 관리 대시보드
            </h2>
            <div className="l-preview-grid">
              <div className="l-preview-copy">
                <h3>오늘 해야 할 일을<br />한 화면에서 확인</h3>
                <p>매일 아침 대시보드를 열면 신규 공고 현황, AI 추천 공고, 마감 임박 알림이 즉시 보입니다.</p>
                <ul className="l-check-list">
                  {[
                    "AI 점수순으로 정렬된 오늘의 추천 공고",
                    "마감 D-3 이내 긴급 공고 빨간 알림",
                    "클릭 한 번으로 제안서 초안 생성 시작",
                    "월별 제안 현황 및 분야별 수주율 차트",
                  ].map((t) => (
                    <li key={t}><span className="l-check-mark">&#10003;</span>{t}</li>
                  ))}
                </ul>
              </div>
              <div className="l-screen-mock">
                <div className="l-mock-bar">
                  <div className="l-dot" style={{ background: "#FF5F56" }} />
                  <div className="l-dot" style={{ background: "#FFBD2E" }} />
                  <div className="l-dot" style={{ background: "#27C93F" }} />
                  <span style={{ color: "rgba(255,255,255,0.28)", fontSize: 11, marginLeft: 8 }}>
                    Proposal Coworker &middot; 대시보드
                  </span>
                </div>
                <div className="l-mock-body">
                  <div className="l-mock-kpis">
                    <div className="l-mk">
                      <div className="l-mk-lbl">신규 공고</div>
                      <div className="l-mk-val">{s?.today_new_bids ?? "-"}</div>
                      <div className="l-mk-sub">&uarr; 실시간</div>
                    </div>
                    <div className="l-mk">
                      <div className="l-mk-lbl">AI 추천</div>
                      <div className="l-mk-val">{s?.today_recommended ?? "-"}</div>
                      <div className="l-mk-sub">평균 70+점</div>
                    </div>
                    <div className="l-mk">
                      <div className="l-mk-lbl">마감 임박</div>
                      <div className="l-mk-val" style={{ color: "#FF8A8A" }}>{s?.deadline_urgent ?? "-"}</div>
                      <div className="l-mk-sub" style={{ color: "#FF8A8A" }}>긴급</div>
                    </div>
                  </div>
                  <div className="l-mock-thead">
                    <div className="l-mth">공고명</div>
                    <div className="l-mth">예산</div>
                    <div className="l-mth">마감</div>
                    <div className="l-mth">AI점수</div>
                  </div>
                  <div className="l-mock-row">
                    <div>
                      <div className="l-mr-t">첨단소재 기술사업화 기획</div>
                      <div className="l-mr-s">KEIT &middot; 산업부</div>
                    </div>
                    <div className="l-mr-amt">2.3억</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#FF8A8A" }}>D-2</div>
                    <div><span className="l-sc l-sc-h">88점</span></div>
                  </div>
                  <div className="l-mock-row">
                    <div>
                      <div className="l-mr-t">국가R&D 성과분석 연구</div>
                      <div className="l-mr-s">과학기술정책연구원</div>
                    </div>
                    <div className="l-mr-amt">1.8억</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#FF8A8A" }}>D-5</div>
                    <div><span className="l-sc l-sc-h">82점</span></div>
                  </div>
                  <div className="l-mock-row">
                    <div>
                      <div className="l-mr-t">기술이전 활성화 전략 수립</div>
                      <div className="l-mr-s">과학기술정보통신부</div>
                    </div>
                    <div className="l-mr-amt">9천만</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#E8C87A" }}>D-9</div>
                    <div><span className="l-sc l-sc-m">76점</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="l-cta-wrap">
          <div className="l-cta-inner">
            <div className="l-cta-copy">
              <h3>지금 바로 시작하세요</h3>
              <p>조직 계정으로 로그인하면 즉시 사용 가능합니다. 별도 설치 불필요.</p>
            </div>
            <a href="/login" className="btn-cta">로그인하기 &rarr;</a>
          </div>
        </div>

        {/* FOOTER */}
        <footer className="l-footer">
          <div className="l-foot-left">&copy; 2026 Proposal Coworker &middot; TENOPA 사내 플랫폼 &middot; 외부 공유 금지</div>
          <div className="l-foot-right">
            <a href="#">사용 가이드</a>
            <a href="mailto:admin@tenopa.co.kr">admin@tenopa.co.kr</a>
            <a href="#">개인정보 처리방침</a>
          </div>
        </footer>
      </div>
    </>
  );
}
