import { ReactNode } from 'react';

interface DefinitionBoxProps {
  children: ReactNode;
}

export default function DefinitionBox({ children }: DefinitionBoxProps) {
  return (
    <div className="definition-box">
      {children}
    </div>
  );
}
