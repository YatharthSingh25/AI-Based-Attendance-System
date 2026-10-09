import React from 'react'

export const Card: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => {
  return (
    <div className="card">
      <div className="card-header">{title}</div>
      <div className="card-body">{children}</div>
    </div>
  )
}

export const Table: React.FC<{ 
  headers: string[]; 
  rows: string[][]; 
  responsive?: boolean 
}> = ({ headers, rows, responsive = true }) => {
  const isResponsive = responsive
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export const Badge: React.FC<{ 
  text: string; 
  variant?: 'success' | 'warning' | 'danger' | 'secondary' 
}> = ({ text, variant = 'secondary' }) => {
  const variants: Record<string, string> = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-orange-100 text-orange-800',
    danger: 'bg-red-100 text-red-800',
    secondary: 'bg-gray-100 text-gray-800',
  }
  const className = variants[variant] || variants.secondary
  return <span className={`badge ${className}`}>{text}</span>
}