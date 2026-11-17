import React from 'react'

export const Card: React.FC<{
  title?: string
  className?: string
  children: React.ReactNode
}> = ({ title, className, children }) => {
  return (
    <div className={className ? `card ${className}` : 'card'}>
      {title ? <div className="card-header">{title}</div> : null}
      <div className="card-body">{children}</div>
    </div>
  )
}

export const Table: React.FC<{
  headers: React.ReactNode[]
  rows: React.ReactNode[][]
  responsive?: boolean
}> = ({ headers, rows, responsive = true }) => {
  const isResponsive = responsive
  return (
    <div className={isResponsive ? 'table-wrapper' : 'table-wrapper full'}>
      <table>
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={index}>{header}</th>
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
  text?: string
  variant?: 'success' | 'warning' | 'danger' | 'secondary'
  children?: React.ReactNode
}> = ({ text, variant = 'secondary', children }) => {
  const variants: Record<string, string> = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-orange-100 text-orange-800',
    danger: 'bg-red-100 text-red-800',
    secondary: 'bg-gray-100 text-gray-800',
  }
  const className = variants[variant] || variants.secondary
  return <span className={`badge ${className}`}>{children ?? text}</span>
}
