'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader, AlertCircle, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ProjectCard[];
  timestamp: Date;
}

interface ProjectCard {
  id: string;
  project_name: string;
  client_name: string;
  project_year?: number;
  start_date?: string;
  end_date?: string;
  budget_krw?: number;
  summary?: string;
  project_type: string;
  proposal_status?: string;
  result_status?: string;
  execution_status?: string;
  keywords?: string[];
  actual_teams?: any;
  actual_participants?: any;
}

interface ChatResponse {
  answer: string;
  sources: ProjectCard[];
  message: string;
}

export function MasterProjectsChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content:
        '안녕하세요! 👋 TENOPA의 과거 프로젝트를 검색할 수 있습니다.\n\n어떤 프로젝트를 찾으신가요? 예를 들어:\n- "우리가 IoT 프로젝트 한 적 있어?"\n- "서울시와 계약한 프로젝트는?"\n- "2023년에 진행했던 공공사업은?"\n- "클라우드 기술을 사용한 프로젝트 찾아줘"',
      timestamp: new Date(),
    },
  ]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 메시지 추가 시 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    // 사용자 메시지 추가
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setError(null);
    setIsLoading(true);

    try {
      // Chat API 호출
      const response = await fetch('/api/master-projects/chat/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input.trim(),
          limit: 5,
        }),
      });

      if (!response.ok) {
        throw new Error(`API 오류: ${response.statusText}`);
      }

      const data: ChatResponse = await response.json();

      // AI 답변 추가
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류 발생';
      setError(errorMessage);

      // 에러 메시지 표시
      const errorChatMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `죄송합니다. 오류가 발생했습니다: ${errorMessage}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorChatMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* 헤더 */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          💬 과거 사례 검색
        </h3>
        <p className="text-xs text-gray-500 mt-1">종료 프로젝트에서 자연어로 검색하세요</p>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'max-w-xs lg:max-w-md rounded-lg px-3 py-2 text-sm',
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              )}
            >
              {/* 메시지 텍스트 */}
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {message.content}
              </div>

              {/* 소스 프로젝트 카드 */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.sources.map((project) => (
                    <ProjectSourceCard key={project.id} project={project} />
                  ))}
                </div>
              )}

              {/* 타임스탐프 */}
              <div
                className={cn(
                  'text-xs mt-1 opacity-70',
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                )}
              >
                {message.timestamp.toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        ))}

        {/* 로딩 표시 */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 rounded-lg px-3 py-2 flex items-center gap-2">
              <Loader className="w-4 h-4 animate-spin" />
              <span className="text-sm">검색 중...</span>
            </div>
          </div>
        )}

        {/* 에러 표시 */}
        {error && (
          <div className="flex justify-start">
            <div className="bg-red-50 text-red-700 rounded-lg px-3 py-2 flex items-start gap-2 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <form
        onSubmit={handleSendMessage}
        className="px-4 py-3 border-t border-gray-200 bg-gray-50"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="검색어 입력... (예: IoT 프로젝트, 서울시...)"
            className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

// 프로젝트 소스 카드 컴포넌트
function ProjectSourceCard({ project }: { project: ProjectCard }) {
  return (
    <div className="bg-white bg-opacity-80 rounded border border-gray-300 p-2 text-xs">
      {/* 프로젝트명 + 상태 */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="font-medium text-gray-900 line-clamp-1">
          {project.project_name}
        </div>
        {project.result_status && (
          <span
            className={cn(
              'px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap',
              project.result_status === 'WON'
                ? 'bg-green-100 text-green-700'
                : project.result_status === 'LOST'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-600'
            )}
          >
            {project.result_status === 'WON' ? '수주' : project.result_status === 'LOST' ? '낙찰' : '대기'}
          </span>
        )}
      </div>

      {/* 발주처 + 기간 */}
      <div className="text-gray-700 mb-1">
        {project.client_name && <div>📍 {project.client_name}</div>}
        {project.start_date && project.end_date && (
          <div className="text-gray-600">
            📅 {project.project_year || project.start_date}
          </div>
        )}
      </div>

      {/* 예산 */}
      {project.budget_krw && (
        <div className="text-gray-700 mb-1">
          💰 {Math.round(project.budget_krw / 100000000)}억원
        </div>
      )}

      {/* 키워드 */}
      {project.keywords && project.keywords.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {project.keywords.slice(0, 3).map((kw, idx) => (
            <span key={idx} className="bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded text-xs">
              {kw}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
