import React from 'react';

export function DataTable({
  columns = [],
  data = [],
  keyExtractor,
  emptyMessage = 'No records found',
  onRowClick,
}) {
  return (
    <div className="overflow-x-auto border border-gray-200 rounded-xl bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-left text-xs text-gray-700">
        <thead className="bg-gray-50 uppercase tracking-wider text-gray-500 font-semibold">
          <tr>
            {columns.map((col, i) => (
              <th key={i} className={`px-4 py-3.5 ${col.className || ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-gray-400">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={keyExtractor ? keyExtractor(row) : row.id}
                onClick={() => onRowClick && onRowClick(row)}
                className={onRowClick ? 'hover:bg-gray-50 cursor-pointer transition-colors' : ''}
              >
                {columns.map((col, i) => (
                  <td key={i} className={`px-4 py-3.5 text-sm text-gray-800 ${col.className || ''}`}>
                    {col.cell
                      ? col.cell(row)
                      : col.accessorKey
                      ? String(row[col.accessorKey] ?? '')
                      : null}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
