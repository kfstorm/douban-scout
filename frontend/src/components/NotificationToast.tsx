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
  success: 'text-ctp-green bg-ctp-green/10',
  error: 'text-ctp-red bg-ctp-red/10',
  info: 'text-ctp-blue bg-ctp-blue/10',
  warning: 'text-ctp-yellow bg-ctp-yellow/10',
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
            className={`flex items-start p-4 rounded-lg shadow-lg border border-ctp-surface1 bg-ctp-surface0 animate-slide-in`}
          >
            <div className={`shrink-0 p-1 rounded-md ${colors[n.type]}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="ml-3 flex-1 pt-0.5">
              <p className="text-sm font-medium text-ctp-text">{n.message}</p>
            </div>
            <div className="ml-4 shrink-0 flex">
              <button
                onClick={() => removeNotification(n.id)}
                className="inline-flex text-ctp-overlay0 hover:text-ctp-subtext0"
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
