import { useState, useEffect } from 'react';

/**
 * Responsive breakpoint hook.
 * Returns true when the viewport width is below the given breakpoint.
 *
 * Usage:
 *   const isMobile = useResponsive(768);
 */
export function useResponsive(breakpoint: number = 768): boolean {
  const [isBelow, setIsBelow] = useState(
    typeof window !== 'undefined' ? window.innerWidth < breakpoint : false,
  );

  useEffect(() => {
    const handler = () => setIsBelow(window.innerWidth < breakpoint);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, [breakpoint]);

  return isBelow;
}
