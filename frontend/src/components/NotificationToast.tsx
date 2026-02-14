import React from 'react';
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useNotificationStore, type NotificationType } from '../store/useNotificationStore';

const icons: Record<NotificationType, React.ElementType> = {
  success: CheckCircleIcon,
  error: ExclamationCircleIcon,
  info: InformationCircleIcon,
  warning: ExclamationTriangleIcon,
};

const colors: Record<NotificationType, string> = {
  success: 'text-green-500 bg-green-50 dark:bg-green-900/20',
  error: 'text-red-500 bg-red-50 dark:bg-red-900/20',
  info: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20',
  warning: 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20',
};

export const NotificationToast: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col gap-2 w-full max-w-sm">
      {notifications.map((n) => {
        const Icon = icons[n.type];
        return (
          <div
            key={n.id}
            className={`flex items-start p-4 rounded-lg shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 animate-slide-in`}
          >
            <div className={`flex-shrink-0 p-1 rounded-md ${colors[n.type]}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="ml-3 flex-1 pt-0.5">
              <p className="text-sm font-medium text-gray-900 dark:text-white">{n.message}</p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                onClick={() => removeNotification(n.id)}
                className="inline-flex text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                aria-label="关闭通知"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};
