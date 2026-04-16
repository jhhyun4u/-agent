# KeyboardShortcutsGuideProps & KeyboardShortcutsGuide
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **KeyboardShortcutsGuideProps** (C:\project\tenopa proposer\frontend\components\KeyboardShortcutsGuide.tsx) -- 1 connections
  - <- contains <- [[keyboardshortcutsguide]]
- **KeyboardShortcutsGuide** (C:\project\tenopa proposer\frontend\components\KeyboardShortcutsGuide.tsx) -- 1 connections
  - -> contains -> [[keyboardshortcutsguideprops]]

## Internal Relationships
- KeyboardShortcutsGuide -> contains -> KeyboardShortcutsGuideProps [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 KeyboardShortcutsGuideProps, KeyboardShortcutsGuide를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 KeyboardShortcutsGuide.tsx이다.

### Key Facts
- interface KeyboardShortcutsGuideProps { open: boolean; onClose: () => void; }
- /** * KeyboardShortcutsGuide — 단축키 가이드 오버레이 * Ctrl+/ 또는 ? 키로 토글 */
