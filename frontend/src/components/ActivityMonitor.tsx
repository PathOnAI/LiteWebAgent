// ActivityMonitor.tsx
import React, { useState, useEffect, useCallback } from 'react';

interface ActivityMonitorProps {
    onInactive: () => void;
    isRunning: boolean;
    isSessionActive: boolean;
    timeoutDuration?: number;
}

const ActivityMonitor: React.FC<ActivityMonitorProps> = ({ 
    onInactive, 
    isRunning, 
    isSessionActive,
    timeoutDuration = 60 // 60 seconds default
}) => {
    const [timeLeft, setTimeLeft] = useState<number>(timeoutDuration);
    
    // Reset timer to full duration
    const resetTimer = useCallback(() => {
        setTimeLeft(timeoutDuration);
    }, [timeoutDuration]);

    // Handle user activity
    useEffect(() => {
        const handleActivity = () => {
            resetTimer();
        };

        // Only track these events if we're in an active session but not running
        if (isSessionActive && !isRunning) {
            window.addEventListener('mousemove', handleActivity);
            window.addEventListener('keypress', handleActivity);
            window.addEventListener('click', handleActivity);
            
            return () => {
                window.removeEventListener('mousemove', handleActivity);
                window.removeEventListener('keypress', handleActivity);
                window.removeEventListener('click', handleActivity);
            };
        }
    }, [resetTimer, isSessionActive, isRunning]);

    // Countdown timer
    useEffect(() => {
        let interval: NodeJS.Timeout | undefined;
        
        if (isSessionActive && !isRunning && timeLeft > 0) {
            interval = setInterval(() => {
                setTimeLeft(time => {
                    if (time <= 1) {
                        if (interval) clearInterval(interval);
                        onInactive();
                        return 0;
                    }
                    return time - 1;
                });
            }, 1000);
        }

        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [timeLeft, onInactive, isSessionActive, isRunning]);

    // Reset timer when running state changes
    useEffect(() => {
        if (isRunning) {
            resetTimer();
        }
    }, [isRunning, resetTimer]);

    if (!isSessionActive) {
        return null;
    }

    // Determine color based on time left
    const getColor = () => {
        if (timeLeft > 30) return 'bg-green-500';
        if (timeLeft > 10) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="flex items-center space-x-2">
            <div className="text-sm font-medium text-gray-600">
                {Math.floor(timeLeft)}s
            </div>
            <div className={`w-2 h-2 rounded-full ${getColor()}`} />
        </div>
    );
};

export default ActivityMonitor;