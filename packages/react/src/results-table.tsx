'use client'

import React from 'react'
import type { AnalysisResult } from './types'

export function ResultsTable({ results }: { results: AnalysisResult[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b">
            <th className="text-left p-2">Score</th>
            <th className="text-left p-2">Verdict</th>
            <th className="text-left p-2">MELA</th>
            <th className="text-left p-2">Noise</th>
            <th className="text-left p-2">ELA</th>
            <th className="text-left p-2">Reasons</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={i} className="border-b hover:bg-muted/50">
              <td className="p-2 font-medium">{r.score}/100</td>
              <td className="p-2">
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    r.verdict === 'authentique'
                      ? 'bg-green-100 text-green-800'
                      : r.verdict === 'suspect'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                  }`}
                >
                  {r.verdict_label}
                </span>
              </td>
              <td className="p-2">{r.signals.mela.score}</td>
              <td className="p-2">{r.signals.noise.score}</td>
              <td className="p-2">{r.signals.ela.score}</td>
              <td className="p-2 text-sm text-muted-foreground max-w-xs truncate">
                {r.reasons.join('; ')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
