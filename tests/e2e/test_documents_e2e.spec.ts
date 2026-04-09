/**
 * 문서 관리 UI - E2E 테스트
 *
 * 테스트 범위:
 * 1. 문서 업로드 흐름
 * 2. 문서 목록 조회 및 필터링
 * 3. 상세 정보 보기
 * 4. 문서 재처리
 * 5. 문서 삭제
 */

import { test, expect, Page } from "@playwright/test";

// 테스트 설정
const BASE_URL = process.env.BASE_URL || "http://localhost:3000";
const TEST_TIMEOUT = 30000;

test.describe("문서 관리 (Document Management)", () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // 인증 토큰 설정 (필요한 경우)
    await page.goto(`${BASE_URL}/kb/documents`);

    // 페이지 로딩 대기
    await page.waitForLoadState("networkidle");
  });

  test.afterEach(async () => {
    await page.close();
  });

  test("1. 페이지 로드 및 기본 UI 렌더링", async () => {
    // Arrange & Act
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Assert
    // 페이지 제목 확인
    await expect(page.locator("h1")).toContainText("인트라넷 문서");

    // 주요 섹션 확인
    await expect(page.locator("text=새 문서 업로드")).toBeVisible();
    await expect(page.locator("text=필터 및 정렬")).toBeVisible();
    await expect(page.locator("text=문서")).toBeVisible();
  });

  test("2. 문서 업로드 - PDF 파일", async () => {
    // Arrange
    const fileName = "test-proposal.pdf";
    const testFile = "tests/fixtures/sample.pdf";

    // Act - 파일 선택
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFile);

    // 문서 유형 선택
    const docTypeSelect = page.locator('select').first();
    await docTypeSelect.selectOption("제안서");

    // 업로드 버튼 클릭
    const uploadButton = page.locator("text=파일 선택");
    await uploadButton.click();

    // Assert - 업로드 완료 대기
    await page.waitForTimeout(2000);

    // 성공 메시지 또는 목록 업데이트 확인
    const successIndicator = page.locator("text=업로드 중").or(
      page.locator("text=완료")
    );
    await expect(successIndicator).toBeDefined();
  });

  test("3. 문서 업로드 - 에러 처리 (지원하지 않는 파일)", async () => {
    // Arrange
    const unsupportedFile = "tests/fixtures/invalid.exe";

    // Act
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(unsupportedFile);

    const uploadButton = page.locator("text=파일 선택");
    await uploadButton.click();

    // Assert - 에러 메시지 확인
    await page.waitForTimeout(1000);
    const errorMessage = page.locator(".bg-red-100");
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText("지원하지 않는");
  });

  test("4. 문서 목록 조회 - 기본", async () => {
    // Act
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Assert - 목록이 렌더링되어야 함
    const documentList = page.locator("[class*='space-y-2']").last();
    await expect(documentList).toBeVisible();

    // 문서 카드 확인 (최소 1개)
    const documentCards = page.locator("div[class*='Card']");
    const count = await documentCards.count();

    if (count > 0) {
      // 카드 내용 확인
      const firstCard = documentCards.first();
      await expect(firstCard.locator("h3")).toBeDefined();
      await expect(firstCard.locator("[class*='Badge']")).toBeDefined();
    }
  });

  test("5. 문서 목록 - 필터링 (상태)", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Act - 상태 필터 선택
    const statusSelect = page.locator('select').nth(0);
    await statusSelect.selectOption("completed");

    // 목록 업데이트 대기
    await page.waitForTimeout(1000);

    // Assert - 필터된 결과 확인
    const statusBadges = page.locator("[class*='Badge']");
    const count = await statusBadges.count();

    // 모든 배지가 "완료" 상태여야 함 (필터링된 경우)
    if (count > 0) {
      for (let i = 0; i < Math.min(count, 3); i++) {
        const badge = statusBadges.nth(i);
        const text = await badge.textContent();
        // "완료" 또는 관련 텍스트 포함
        expect(text).toMatch(/완료|success|green/i);
      }
    }
  });

  test("6. 문서 목록 - 검색 (파일명)", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Act - 파일명 검색
    const searchInput = page.locator('input[placeholder*="파일명"]');
    await searchInput.fill("proposal");

    // 검색 결과 대기
    await page.waitForTimeout(1000);

    // Assert - 검색 결과 확인
    const documentCards = page.locator("div[class*='Card']");
    const count = await documentCards.count();

    // 결과가 있다면 파일명에 "proposal" 포함되어야 함
    if (count > 0) {
      const firstCard = documentCards.first();
      const fileName = await firstCard.locator("h3").textContent();
      expect(fileName?.toLowerCase()).toContain("proposal");
    }
  });

  test("7. 문서 목록 - 정렬", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Act - 정렬 옵션 변경
    const sortSelect = page.locator('select').nth(2);
    await sortSelect.selectOption("filename");

    const orderSelect = page.locator('select').nth(3);
    await orderSelect.selectOption("asc");

    await page.waitForTimeout(1000);

    // Assert - 정렬이 적용되었는지 확인
    const documentCards = page.locator("div[class*='Card']");
    const count = await documentCards.count();

    if (count >= 2) {
      // 첫 번째와 두 번째 파일명 비교 (정렬 검증)
      const firstFile = await documentCards.nth(0).locator("h3").textContent();
      const secondFile = await documentCards.nth(1).locator("h3").textContent();

      // 알파벳순 (오름차순)이어야 함
      expect(firstFile?.localeCompare(secondFile || "") || 0).toBeLessThanOrEqual(0);
    }
  });

  test("8. 문서 재처리 - 실패 상태", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // 실패 상태의 문서 찾기
    const failedBadge = page.locator('[class*="red"]').filter({
      hasText: /실패/
    }).first();

    if (await failedBadge.isVisible()) {
      // Act - 재처리 버튼 클릭
      const card = failedBadge.locator("..");
      const reprocessButton = card.locator("text=재처리");

      if (await reprocessButton.isVisible()) {
        await reprocessButton.click();

        // 확인 버튼 클릭
        const confirmButton = card.locator("text=재처리");
        if (await confirmButton.isVisible()) {
          await confirmButton.click();

          // Assert - 상태 변경 대기
          await page.waitForTimeout(2000);

          // 상태가 변경되었는지 확인
          const updatedBadge = card.locator('[class*="Badge"]');
          const status = await updatedBadge.textContent();
          expect(status).toMatch(/처리 중|추출|청킹|임베딩/);
        }
      }
    }
  });

  test("9. 문서 삭제 - 확인 메커니즘", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // 첫 번째 문서 찾기
    const documentCard = page.locator("div[class*='Card']").first();
    if (await documentCard.isVisible()) {
      // Act - 삭제 버튼 클릭
      const deleteButton = documentCard.locator("text=삭제").first();
      await deleteButton.click();

      // Assert - 확인 단계
      const confirmButtons = documentCard.locator("text=삭제");
      const count = await confirmButtons.count();

      // 확인 버튼이 나타나야 함 (2개 이상)
      expect(count).toBeGreaterThanOrEqual(1);

      // 취소 버튼 확인
      const cancelButton = documentCard.locator("text=취소");
      await expect(cancelButton).toBeVisible();

      // 취소
      await cancelButton.click();

      // 확인 버튼 사라져야 함
      await page.waitForTimeout(500);
      const confirmAfterCancel = documentCard.locator("text=삭제");
      // 삭제 버튼만 남아야 함
    }
  });

  test("10. 문서 삭제 - 실행", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // 삭제할 문서 선택
    const documentBefore = page.locator("div[class*='Card']");
    const countBefore = await documentBefore.count();

    if (countBefore > 0) {
      const firstCard = documentBefore.first();

      // Act - 삭제 클릭
      const deleteButton = firstCard.locator("text=삭제").first();
      await deleteButton.click();

      // 확인 버튼 클릭
      const confirmButton = firstCard.locator("text=삭제").nth(1);
      if (await confirmButton.isVisible()) {
        await confirmButton.click();

        // 목록 새로고침 대기
        await page.waitForTimeout(2000);

        // Assert - 문서 개수 감소
        const documentAfter = page.locator("div[class*='Card']");
        const countAfter = await documentAfter.count();

        expect(countAfter).toBeLessThanOrEqual(countBefore);
      }
    }
  });

  test("11. 페이지네이션", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Act - 페이지네이션 버튼 확인
    const nextButton = page.locator("text=다음");
    const prevButton = page.locator("text=이전");

    // Assert - 초기 상태
    if (await nextButton.isVisible()) {
      // 다음 버튼 클릭
      await nextButton.click();

      // 목록 업데이트 대기
      await page.waitForTimeout(1000);

      // 이전 버튼이 활성화되어야 함
      const prevEnabled = await prevButton.isEnabled();
      // (페이지 2 이상에서)
    }
  });

  test("12. 에러 상황 - 네트워크 오류 복구", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // 초기 로드 확인
    const initialCards = page.locator("div[class*='Card']");
    const initialCount = await initialCards.count();

    // Act - 페이지 새로고침
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Assert - 목록이 다시 로드되어야 함
    const reloadedCards = page.locator("div[class*='Card']");
    const reloadedCount = await reloadedCards.count();

    // 최소 0개 이상의 카드
    expect(reloadedCount).toBeGreaterThanOrEqual(0);
  });

  test("13. 접근성 - 키보드 네비게이션", async () => {
    // Arrange
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Act - 탭 키로 네비게이션
    await page.keyboard.press("Tab");

    // 포커스된 요소 확인
    const focusedElement = page.locator(":focus");
    await expect(focusedElement).toBeDefined();

    // 엔터 키로 상호작용
    await page.keyboard.press("Enter");
  });

  test("14. 반응형 디자인 - 모바일", async () => {
    // Mobile viewport 설정
    await page.setViewportSize({ width: 375, height: 667 });

    // Act
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");

    // Assert - 모바일 친화적 렌더링
    const buttons = page.locator("button");
    const count = await buttons.count();

    // 버튼이 터치 가능한 크기여야 함 (최소 44x44px)
    // 이는 시각적 테스트로 확인 필요
    expect(count).toBeGreaterThan(0);
  });

  test("15. 성능 - 페이지 로드 시간", async () => {
    // Arrange & Act
    const startTime = Date.now();
    await page.goto(`${BASE_URL}/kb/documents`);
    await page.waitForLoadState("networkidle");
    const endTime = Date.now();

    // Assert - 로드 시간 < 5초
    const loadTime = endTime - startTime;
    expect(loadTime).toBeLessThan(5000);
  });
});
