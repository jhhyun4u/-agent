"use client";

/**
 * ProposalEditor — Tiptap 기반 제안서 에디터 (§13-10)
 *
 * - Tiptap starter-kit + Highlight (AI 코멘트)
 * - 섹션별 편집
 * - 자동 저장 (debounce 3초)
 */

import { useCallback, useEffect, useRef } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Highlight from "@tiptap/extension-highlight";

interface ProposalEditorProps {
  content: string;
  onUpdate: (html: string) => void;
  className?: string;
}

export default function ProposalEditor({
  content,
  onUpdate,
  className = "",
}: ProposalEditorProps) {
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Highlight.configure({
        multicolor: true,
        HTMLAttributes: {
          class: "bg-amber-500/20 text-amber-200 rounded px-0.5",
        },
      }),
    ],
    content,
    editorProps: {
      attributes: {
        class:
          "prose prose-invert prose-sm max-w-none min-h-[400px] focus:outline-none px-6 py-4 text-[#ededed] leading-relaxed",
      },
    },
    onUpdate({ editor: ed }) {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        onUpdate(ed.getHTML());
      }, 3000);
    },
  });

  // content가 외부에서 변경되면 에디터 갱신
  useEffect(() => {
    if (editor && content && editor.getHTML() !== content) {
      editor.commands.setContent(content, { emitUpdate: false });
    }
  }, [editor, content]);

  // 언마운트 시 debounce flush
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  if (!editor) {
    return (
      <div className="flex items-center justify-center h-64 text-[#8c8c8c] text-sm">
        에디터 로딩 중...
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* 도구바 */}
      <Toolbar editor={editor} />

      {/* 에디터 본문 */}
      <div className="flex-1 overflow-y-auto bg-[#111111]">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

// ── 도구바 ──

function Toolbar({ editor }: { editor: ReturnType<typeof useEditor> }) {
  if (!editor) return null;

  const btn = (
    label: string,
    active: boolean,
    onClick: () => void
  ) => (
    <button
      onClick={onClick}
      className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
        active
          ? "bg-[#3ecf8e]/20 text-[#3ecf8e]"
          : "text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626]"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex items-center gap-0.5 px-3 py-1.5 bg-[#1c1c1c] border-b border-[#262626] flex-wrap">
      {btn("B", editor.isActive("bold"), () =>
        editor.chain().focus().toggleBold().run()
      )}
      {btn("I", editor.isActive("italic"), () =>
        editor.chain().focus().toggleItalic().run()
      )}
      {btn("U̲", editor.isActive("underline"), () =>
        editor.chain().focus().toggleStrike().run()
      )}

      <div className="w-px h-4 bg-[#262626] mx-1" />

      {btn("H1", editor.isActive("heading", { level: 1 }), () =>
        editor.chain().focus().toggleHeading({ level: 1 }).run()
      )}
      {btn("H2", editor.isActive("heading", { level: 2 }), () =>
        editor.chain().focus().toggleHeading({ level: 2 }).run()
      )}
      {btn("H3", editor.isActive("heading", { level: 3 }), () =>
        editor.chain().focus().toggleHeading({ level: 3 }).run()
      )}

      <div className="w-px h-4 bg-[#262626] mx-1" />

      {btn("• 목록", editor.isActive("bulletList"), () =>
        editor.chain().focus().toggleBulletList().run()
      )}
      {btn("1. 목록", editor.isActive("orderedList"), () =>
        editor.chain().focus().toggleOrderedList().run()
      )}
      {btn("인용", editor.isActive("blockquote"), () =>
        editor.chain().focus().toggleBlockquote().run()
      )}

      <div className="w-px h-4 bg-[#262626] mx-1" />

      {btn("하이라이트", editor.isActive("highlight"), () =>
        editor.chain().focus().toggleHighlight().run()
      )}
    </div>
  );
}
