import {
  ChevronLeftIcon as RadixChevronLeft,
  ChevronRightIcon as RadixChevronRight,
  ChevronDownIcon as RadixChevronDown,
  CheckIcon as RadixCheckIcon,
  ReaderIcon as RadixReaderIcon,
  CodeIcon as RadixCodeIcon,
  LightningBoltIcon as RadixLightningBoltIcon,
  StarIcon as RadixStarIcon,
  DotFilledIcon as RadixDotFilledIcon,
  InfoCircledIcon as RadixInfoCircledIcon,
  CrossCircledIcon as RadixCrossCircledIcon,
  CheckCircledIcon as RadixCheckCircledIcon,
} from '@radix-ui/react-icons';
import React from 'react';

type IconProps = React.SVGAttributes<SVGElement>;

const createIcon = (name: string, path: React.ReactNode) => {
  const Icon = React.forwardRef<SVGSVGElement, IconProps>(
    ({ width = 15, height = 15, ...props }, ref) => (
      <svg
        ref={ref}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 15 15"
        fill="none"
        width={width}
        height={height}
        {...props}
      >
        {path}
      </svg>
    ),
  );
  Icon.displayName = name;
  return Icon;
};

export const MoonIcon = createIcon(
  'MoonIcon',
  <>
    <path
      d="M7.5 1.5C4.5 1.5 2 4 2 7.5C2 11 4.5 13.5 7.5 13.5C10.5 13.5 13 11 13 7.5C11.5 8.5 9.5 8.5 8 7C6.5 5.5 6.5 3.5 7.5 1.5Z"
      fill="currentColor"
    />
  </>,
);

export const SunIcon = createIcon(
  'SunIcon',
  <>
    <circle cx="7.5" cy="7.5" r="2.5" fill="currentColor" />
    <path
      d="M7.5 1V2.5M7.5 12.5V14M14 7.5H12.5M2.5 7.5H1M12.5 3.5L11.5 4.5M4.5 10.5L3.5 11.5M12.5 11.5L11.5 10.5M4.5 4.5L3.5 3.5"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const SettingsIcon = createIcon(
  'SettingsIcon',
  <>
    <path
      d="M7.5 9.5C8.6 9.5 9.5 8.6 9.5 7.5C9.5 6.4 8.6 5.5 7.5 5.5C6.4 5.5 5.5 6.4 5.5 7.5C5.5 8.6 6.4 9.5 7.5 9.5Z"
      fill="currentColor"
    />
    <path
      d="M11.5 7.5C11.5 7.2 11.5 6.8 11.4 6.5L12.7 5.5L12 4.2L10.5 4.8C10.1 4.5 9.7 4.2 9.2 4L9 2.5H7.5L7.3 4C6.8 4.2 6.4 4.5 6 4.8L4.5 4.2L3.8 5.5L5.1 6.5C5 6.8 5 7.2 5 7.5C5 7.8 5 8.2 5.1 8.5L3.8 9.5L4.5 10.8L6 10.2C6.4 10.5 6.8 10.8 7.3 11L7.5 12.5H9L9.2 11C9.7 10.8 10.1 10.5 10.5 10.2L12 10.8L12.7 9.5L11.4 8.5C11.5 8.2 11.5 7.8 11.5 7.5Z"
      fill="currentColor"
    />
  </>,
);

export const LogOutIcon = createIcon(
  'LogOutIcon',
  <>
    <path
      d="M5.5 12.5H3.5C2.9 12.5 2.5 12.1 2.5 11.5V3.5C2.5 2.9 2.9 2.5 3.5 2.5H5.5"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
    <path
      d="M10 11L12.5 7.5L10 4"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M12.5 7.5H5.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
  </>,
);

export const UserIcon = createIcon(
  'UserIcon',
  <>
    <circle cx="7.5" cy="5" r="2.5" fill="currentColor" />
    <path
      d="M2.5 13C2.5 10.5 4.7 8.5 7.5 8.5C10.3 8.5 12.5 10.5 12.5 13"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const XIcon = createIcon(
  'XIcon',
  <>
    <path d="M4 4L11 11M11 4L4 11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
  </>,
);

export const MenuIcon = createIcon(
  'MenuIcon',
  <>
    <path
      d="M2 4H13M2 7.5H13M2 11H13"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const GraduationCapIcon = createIcon(
  'GraduationCapIcon',
  <>
    <path d="M7.5 5L1.5 8L7.5 11L13.5 8L7.5 5Z" fill="currentColor" />
    <path
      d="M3.5 9.5V12.5C3.5 12.5 5 14 7.5 14C10 14 11.5 12.5 11.5 12.5V9.5"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M13.5 8V12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
  </>,
);

export const ShuffleIcon = createIcon(
  'ShuffleIcon',
  <>
    <path
      d="M2 11.5L5.5 8L2 4.5"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M13 4.5L9.5 8L13 11.5"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M5.5 8H13M9.5 8H2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
  </>,
);

export const ListIcon = createIcon(
  'ListIcon',
  <>
    <path
      d="M5 2.5H12.5M5 7.5H12.5M5 12.5H12.5M2.5 2.5H2.51M2.5 7.5H2.51M2.5 12.5H2.51"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const LightbulbIcon = createIcon(
  'LightbulbIcon',
  <>
    <path
      d="M7.5 2C5 2 3 4 3 6.5C3 8.5 4.5 9.5 5.5 10.5V11.5C5.5 12 6 12.5 6.5 12.5H8.5C9 12.5 9.5 12 9.5 11.5V10.5C10.5 9.5 12 8.5 12 6.5C12 4 10 2 7.5 2Z"
      fill="currentColor"
    />
    <path d="M6 13.5H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
  </>,
);

export const EyeIcon = createIcon(
  'EyeIcon',
  <>
    <path
      d="M7.5 5C5.5 5 3.5 7.5 2.5 8.5C3.5 9.5 5.5 12 7.5 12C9.5 12 11.5 9.5 12.5 8.5C11.5 7.5 9.5 5 7.5 5Z"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
    <circle cx="7.5" cy="8.5" r="1.5" fill="currentColor" />
  </>,
);

export const EyeOffIcon = createIcon(
  'EyeOffIcon',
  <>
    <path
      d="M2.5 2.5L12.5 12.5M5 5.5C3.5 6.5 2.5 7.5 2.5 8.5C3.5 9.5 5.5 12 7.5 12C8.5 12 9.5 11.5 10.5 10.5M12.5 8.5C11.5 7.5 9.5 5 7.5 5C7 5 6.5 5.1 6 5.2"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const FileTextIcon = createIcon(
  'FileTextIcon',
  <>
    <path
      d="M3.5 2.5H11.5V12.5H3.5V2.5Z"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M5.5 5.5H9.5M5.5 8H8.5"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const Loader2Icon = createIcon(
  'Loader2Icon',
  <>
    <path
      d="M7.5 1.5V4M7.5 11V13.5M13.5 7.5H11M4 7.5H1.5M12 4L10 6M5 10L3 12M12 11L10 9M5 5L3 3"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
    />
  </>,
);

export const MessageSquareIcon = createIcon(
  'MessageSquareIcon',
  <>
    <path
      d="M2.5 10.5V3.5C2.5 2.9 2.9 2.5 3.5 2.5H11.5C12.1 2.5 12.5 2.9 12.5 3.5V8.5C12.5 9.1 12.1 9.5 11.5 9.5H5.5L2.5 10.5Z"
      fill="currentColor"
    />
  </>,
);

export {
  RadixChevronLeft,
  RadixChevronRight,
  RadixChevronDown,
  RadixCheckIcon,
  RadixReaderIcon,
  RadixCodeIcon,
  RadixLightningBoltIcon,
  RadixStarIcon,
  RadixDotFilledIcon,
  RadixInfoCircledIcon,
  RadixCrossCircledIcon,
  RadixCheckCircledIcon,
};
