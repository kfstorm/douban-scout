import React from 'react';
import type { ImportStatus } from '../types/movie';

interface ImportStatusProps {
  status: ImportStatus;
}

export const ImportStatusBanner: React.FC<ImportStatusProps> = ({ status }) => {
  if (status.status === 'idle') return null;

  const getStatusColor = () => {
    switch (status.status) {
      case 'running':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'running':
        return '正在导入数据...';
      case 'completed':
        return '导入完成！';
      case 'failed':
        return `导入失败: ${status.message}`;
      default:
        return '';
    }
  };

  return (
    <div className={`${getStatusColor()} px-4 py-3 rounded-lg mb-4`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">{getStatusText()}</p>
          {status.status === 'running' && (
            <p className="text-sm mt-1">
              已处理: {status.processed.toLocaleString()} / {status.total.toLocaleString()} (
              {status.percentage.toFixed(1)}%)
            </p>
          )}
        </div>

        {status.status === 'running' && (
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-current" />
        )}
      </div>

      {status.status === 'running' && (
        <div className="mt-3 w-full bg-white dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-current h-2 rounded-full transition-all duration-300"
            style={{ width: `${status.percentage}%` }}
          />
        </div>
      )}
    </div>
  );
};
