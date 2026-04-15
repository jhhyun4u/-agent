"use client";

/**
 * Vault Search Bar Component
 * Quick search interface for vault queries
 */

import { useState } from "react";
import { Search, ChevronDown } from "lucide-react";

interface VaultSearchBarProps {
  onSearch?: (query: string, section?: string) => void;
}

const SECTIONS = [
  { id: "all", label: "모든 섹션" },
  { id: "completed_projects", label: "완료된 프로젝트" },
  { id: "government_guidelines", label: "발주기관 지침" },
  { id: "market_prices", label: "시장 가격" },
  { id: "lessons_learned", label: "교훈" },
];

export default function VaultSearchBar({ onSearch }: VaultSearchBarProps) {
  const [query, setQuery] = useState("");
  const [selectedSection, setSelectedSection] = useState("all");
  const [isOpen, setIsOpen] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch?.(
        query,
        selectedSection === "all" ? undefined : selectedSection
      );
    }
  };

  return (
    <form onSubmit={handleSearch} className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="지식 검색..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-4 py-3 pl-10 bg-[#2d2d2d] border border-[#404040] text-white rounded-lg focus:outline-none focus:border-[#10a37f] text-sm"
          />
          <Search className="absolute left-3 top-3.5 w-4 h-4 text-[#888888]" />
        </div>

        <div className="relative">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="px-4 py-3 bg-[#2d2d2d] border border-[#404040] text-white rounded-lg hover:border-[#10a37f] transition-colors flex items-center gap-2 text-sm"
          >
            {SECTIONS.find((s) => s.id === selectedSection)?.label}
            <ChevronDown className="w-4 h-4" />
          </button>

          {isOpen && (
            <div className="absolute top-full left-0 mt-2 w-48 bg-[#2d2d2d] border border-[#404040] rounded-lg shadow-lg z-10">
              {SECTIONS.map((section) => (
                <button
                  key={section.id}
                  type="button"
                  onClick={() => {
                    setSelectedSection(section.id);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                    selectedSection === section.id
                      ? "bg-[#10a37f] text-white"
                      : "text-[#e5e5e5] hover:bg-[#404040]"
                  }`}
                >
                  {section.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={!query.trim()}
          className="px-6 py-3 bg-[#10a37f] hover:bg-[#1a9970] text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          검색
        </button>
      </div>

      <div className="text-xs text-[#888888]">
        팁: 특정 섹션에서 검색하거나 여러 섹션을 함께 검색할 수 있습니다
      </div>
    </form>
  );
}
