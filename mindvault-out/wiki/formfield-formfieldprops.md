# FormField & FormFieldProps
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **FormField** (C:\project\tenopa proposer\frontend\components\ui\FormField.tsx) -- 5 connections
  - -> contains -> [[formfieldprops]]
  - -> contains -> [[textinputprops]]
  - -> contains -> [[textareaprops]]
  - -> contains -> [[selectprops]]
  - -> imports -> [[unresolvedrefreact]]
- **FormFieldProps** (C:\project\tenopa proposer\frontend\components\ui\FormField.tsx) -- 1 connections
  - <- contains <- [[formfield]]
- **SelectProps** (C:\project\tenopa proposer\frontend\components\ui\FormField.tsx) -- 1 connections
  - <- contains <- [[formfield]]
- **TextAreaProps** (C:\project\tenopa proposer\frontend\components\ui\FormField.tsx) -- 1 connections
  - <- contains <- [[formfield]]
- **TextInputProps** (C:\project\tenopa proposer\frontend\components\ui\FormField.tsx) -- 1 connections
  - <- contains <- [[formfield]]

## Internal Relationships
- FormField -> contains -> FormFieldProps [EXTRACTED]
- FormField -> contains -> TextInputProps [EXTRACTED]
- FormField -> contains -> TextAreaProps [EXTRACTED]
- FormField -> contains -> SelectProps [EXTRACTED]

## Cross-Community Connections
- FormField -> imports -> __unresolved__::ref::_react_ (-> [[unresolvedrefreact-unresolvedreflibapi]])

## Context
이 커뮤니티는 FormField, FormFieldProps, SelectProps를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 FormField.tsx이다.

### Key Facts
- interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; error?: string; helperText?: string; required?: boolean; children: React.ReactNode; }
- interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; error?: string; helperText?: string; required?: boolean; children: React.ReactNode; }
- interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> { label?: string; error?: string; helperText?: string; options: Array<{ value: string; label: string }>; }
- interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> { label?: string; error?: string; helperText?: string; }
- interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> { label?: string; error?: string; helperText?: string; }
