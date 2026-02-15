import React, { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { SunIcon, MoonIcon, ComputerDesktopIcon, CheckIcon } from '@heroicons/react/24/outline';
import { useTheme, type Theme } from '../hooks/useTheme';

const themes: { id: Theme; name: string; icon: typeof SunIcon }[] = [
  { id: 'system', name: '自动模式', icon: ComputerDesktopIcon },
  { id: 'light', name: '浅色模式', icon: SunIcon },
  { id: 'dark', name: '深色模式', icon: MoonIcon },
];

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme } = useTheme();

  const CurrentIcon = themes.find((t) => t.id === theme)?.icon || ComputerDesktopIcon;

  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button
          className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          title="切换主题"
        >
          <CurrentIcon className="w-5 h-5" />
        </Menu.Button>
      </div>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-36 origin-top-right divide-y divide-gray-100 rounded-md bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
          <div className="px-1 py-1">
            {themes.map((t) => (
              <Menu.Item key={t.id}>
                {({ active }) => (
                  <button
                    onClick={() => setTheme(t.id)}
                    className={`${
                      active ? 'bg-primary-500 text-white' : 'text-gray-900 dark:text-gray-200'
                    } group flex w-full items-center justify-between rounded-md px-2 py-2 text-sm transition-colors`}
                  >
                    <div className="flex items-center gap-2">
                      <t.icon className="w-4 h-4" />
                      {t.name}
                    </div>
                    {theme === t.id && <CheckIcon className="w-4 h-4" />}
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
};
