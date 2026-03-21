/**
 * TENOPA 조직 초기 데이터 (tenopa team structure.xlsx 기반)
 * API에서 데이터를 못 가져올 때 폴백으로 사용
 */

export interface SeedDivision {
  id: string;
  name: string;
  head?: SeedMember;       // 본부장/소장
  teams: SeedTeam[];
}

export interface SeedTeam {
  id: string;
  name: string;
  specialty: string;
  members: SeedMember[];
}

export interface SeedMember {
  email: string;
  name: string;
  title: string;
  role: string;
}

export const SEED_ORG: SeedDivision[] = [
  {
    id: "div-rnd", name: "R&D혁신본부",
    head: { email: "hjh@tenopa.co.kr", name: "현재호", title: "대표이사", role: "본부장" },
    teams: [
      {
        id: "team-innov1", name: "혁신1팀",
        specialty: "과학기술인재, 신산업정책, AI안전, 탄소소재, 국토교통, 탄소중립, 기후변화대응",
        members: [
          { email: "hamh7071@tenopa.co.kr", name: "하미함", title: "책임", role: "팀장" },
          { email: "smk97@tenopa.co.kr", name: "성민경", title: "선임", role: "팀원" },
        ],
      },
      {
        id: "team-innov2", name: "혁신2팀",
        specialty: "성과분석, 정밀의료, 동향조사, 감염병, 바이오빅데이터, 바이오헬스",
        members: [
          { email: "heosy@tenopa.co.kr", name: "허선양", title: "수석", role: "팀장" },
          { email: "leesy2586@tenopa.co.kr", name: "이소영", title: "전임", role: "팀원" },
          { email: "1414jy@tenopa.co.kr", name: "김지연", title: "선임", role: "팀원" },
          { email: "parksj@tenopa.co.kr", name: "박선정", title: "선임", role: "팀원" },
          { email: "dabikim@tenopa.co.kr", name: "김다비", title: "전임", role: "팀원" },
          { email: "nej1015@tenopa.co.kr", name: "노의정", title: "전임", role: "팀원" },
          { email: "hayun@tenopa.kr", name: "박하윤", title: "전임", role: "팀원" },
          { email: "jclee@tenopa.co.kr", name: "이정철", title: "전임", role: "팀원" },
        ],
      },
      {
        id: "team-innov3", name: "혁신3팀",
        specialty: "건강관리, 재생의료, 정신건강, 의료기기, 마약류안전관리, 고령친화, 만성질환관리",
        members: [
          { email: "jmk@tenopa.co.kr", name: "전민경", title: "수석", role: "팀장" },
        ],
      },
    ],
  },
  {
    id: "div-vertical", name: "버티컬AX본부",
    head: { email: "yoon@tenopa.co.kr", name: "윤홍권", title: "파트너", role: "본부장" },
    teams: [
      {
        id: "team-ax1", name: "버티컬AX1팀",
        specialty: "AI시티, AI빅데이터, 피지컬AI, 정신건강, 필수의료, 예타기획",
        members: [
          { email: "mkkim@tenopa.co.kr", name: "김민규", title: "책임", role: "팀원" },
          { email: "dhlee@tenopa.co.kr", name: "이동혁", title: "책임", role: "팀원" },
          { email: "woojoon@tenopa.co.kr", name: "윤우준", title: "선임", role: "팀원" },
          { email: "chlee@tenopa.co.kr", name: "이창규", title: "선임", role: "팀원" },
          { email: "heejung@tenopa.co.kr", name: "장의정", title: "선임", role: "팀원" },
        ],
      },
    ],
  },
  {
    id: "div-public", name: "공공AX본부",
    head: { email: "sjk@tenopa.co.kr", name: "김상준", title: "파트너", role: "본부장" },
    teams: [
      {
        id: "team-public1", name: "공공1팀",
        specialty: "재난안전, 원자력, 토양지하수, 환경보험, 유해물질, 재생의료, 양자, 자율제조, 지역혁신",
        members: [
          { email: "sjk@tenopa.co.kr", name: "김상준", title: "파트너", role: "팀장" },
          { email: "ekk@tenopa.co.kr", name: "김의권", title: "수석", role: "팀원" },
          { email: "yrkim@tenopa.co.kr", name: "김유라", title: "책임", role: "팀원" },
          { email: "yjhong@tenopa.co.kr", name: "홍연주", title: "선임", role: "팀원" },
          { email: "kjh1170@tenopa.co.kr", name: "김준하", title: "선임", role: "팀원" },
          { email: "bkkim@tenopa.co.kr", name: "김법경", title: "전임", role: "팀원" },
        ],
      },
    ],
  },
  {
    id: "div-t2b", name: "기술사업화본부",
    head: { email: "ys1218@tenopa.co.kr", name: "최유석", title: "수석", role: "본부장" },
    teams: [
      {
        id: "team-t2b1", name: "기술사업화1팀",
        specialty: "스케일업팁스, 기술사업화, 벤처성장지원, 딥테크챌린지, PMO(프로젝트관리)",
        members: [
          { email: "jhnoh@tenopa.co.kr", name: "노지현", title: "책임", role: "팀원" },
          { email: "yskang@tenopa.co.kr", name: "강윤서", title: "선임", role: "팀원" },
          { email: "shyun@tenopa.co.kr", name: "현상현", title: "선임", role: "팀원" },
        ],
      },
    ],
  },
  {
    id: "div-axhub", name: "AX허브연구소",
    head: { email: "hjh@tenopa.co.kr", name: "현재호", title: "대표이사", role: "소장" },
    teams: [
      {
        id: "team-axhub", name: "AX혁신팀",
        specialty: "AI업무자동화, AI 교육훈련, AX컨설팅",
        members: [
          { email: "hjh@tenopa.co.kr", name: "현재호", title: "대표이사", role: "팀장" },
          { email: "redhood@tenopa.co.kr", name: "김연정", title: "실장", role: "개발" },
          { email: "leedj@tenopa.co.kr", name: "이동주", title: "팀원", role: "개발" },
        ],
      },
    ],
  },
  {
    id: "div-mgmt", name: "경영관리본부",
    teams: [
      {
        id: "team-mgmt", name: "경영기획실",
        specialty: "",
        members: [
          { email: "redhood@tenopa.co.kr", name: "김연정", title: "실장", role: "실장" },
          { email: "jainkim@tenopa.co.kr", name: "김자인", title: "차장", role: "팀원" },
          { email: "bykang93@tenopa.co.kr", name: "강보연", title: "대리", role: "사업관리담당" },
          { email: "wjkim@tenopa.co.kr", name: "김우재", title: "주임", role: "인사총무담당" },
          { email: "jjh@tenopa.co.kr", name: "전진희", title: "주임", role: "사업관리담당" },
        ],
      },
    ],
  },
];

/** 경영진 — 대표이사 */
export const SEED_EXECUTIVES: SeedMember[] = [
  { email: "hjh@tenopa.co.kr", name: "현재호", title: "대표이사", role: "대표이사" },
];
