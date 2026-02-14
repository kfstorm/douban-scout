import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useNotificationStore } from './useNotificationStore';

describe('useNotificationStore', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useNotificationStore.setState({
      notifications: [],
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Initial State', () => {
    it('should have empty notifications array', () => {
      const state = useNotificationStore.getState();
      expect(state.notifications).toEqual([]);
    });
  });

  describe('addNotification', () => {
    it('should add notification with default type', () => {
      useNotificationStore.getState().addNotification('测试消息');
      const notifications = useNotificationStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].message).toBe('测试消息');
      expect(notifications[0].type).toBe('info');
      expect(notifications[0].id).toBeDefined();
    });

    it('should add notification with success type', () => {
      useNotificationStore.getState().addNotification('操作成功', 'success');
      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].type).toBe('success');
    });

    it('should add notification with error type', () => {
      useNotificationStore.getState().addNotification('操作失败', 'error');
      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].type).toBe('error');
    });

    it('should add notification with warning type', () => {
      useNotificationStore.getState().addNotification('警告信息', 'warning');
      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].type).toBe('warning');
    });

    it('should add multiple notifications', () => {
      useNotificationStore.getState().addNotification('消息1');
      useNotificationStore.getState().addNotification('消息2');
      useNotificationStore.getState().addNotification('消息3');
      expect(useNotificationStore.getState().notifications).toHaveLength(3);
    });

    it('should auto remove notification after 5 seconds', () => {
      useNotificationStore.getState().addNotification('测试消息');
      expect(useNotificationStore.getState().notifications).toHaveLength(1);

      vi.advanceTimersByTime(5000);

      expect(useNotificationStore.getState().notifications).toHaveLength(0);
    });

    it('should generate unique ids for each notification', () => {
      useNotificationStore.getState().addNotification('消息1');
      useNotificationStore.getState().addNotification('消息2');
      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].id).not.toBe(notifications[1].id);
    });
  });

  describe('removeNotification', () => {
    it('should remove notification by id', () => {
      useNotificationStore.getState().addNotification('消息1');
      useNotificationStore.getState().addNotification('消息2');

      const notifications = useNotificationStore.getState().notifications;
      const firstId = notifications[0].id;

      useNotificationStore.getState().removeNotification(firstId);

      expect(useNotificationStore.getState().notifications).toHaveLength(1);
      expect(useNotificationStore.getState().notifications[0].message).toBe('消息2');
    });

    it('should do nothing if id does not exist', () => {
      useNotificationStore.getState().addNotification('消息1');
      useNotificationStore.getState().removeNotification('non-existent-id');
      expect(useNotificationStore.getState().notifications).toHaveLength(1);
    });

    it('should handle removing all notifications manually', () => {
      useNotificationStore.getState().addNotification('消息1');
      useNotificationStore.getState().addNotification('消息2');
      useNotificationStore.getState().addNotification('消息3');

      const notifications = useNotificationStore.getState().notifications;
      notifications.forEach((n) => {
        useNotificationStore.getState().removeNotification(n.id);
      });

      expect(useNotificationStore.getState().notifications).toHaveLength(0);
    });
  });

  describe('Auto-remove timing', () => {
    it('should not remove notification before 5 seconds', () => {
      useNotificationStore.getState().addNotification('测试消息');
      vi.advanceTimersByTime(4999);
      expect(useNotificationStore.getState().notifications).toHaveLength(1);
    });

    it('should remove only the expired notification', () => {
      useNotificationStore.getState().addNotification('消息1');
      vi.advanceTimersByTime(2000);
      useNotificationStore.getState().addNotification('消息2');

      vi.advanceTimersByTime(3000);

      expect(useNotificationStore.getState().notifications).toHaveLength(1);
      expect(useNotificationStore.getState().notifications[0].message).toBe('消息2');
    });
  });
});
