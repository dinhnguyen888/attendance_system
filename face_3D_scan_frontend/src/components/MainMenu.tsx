import { motion } from 'framer-motion';
import type { Employee } from '../types';
import styles from './MainMenu.module.css';

interface MainMenuProps {
  employee: Employee;
  onFaceRegistration: () => void;
  onCheckIn: () => void;
  onCheckOut: () => void;
}

export const MainMenu = ({ employee, onFaceRegistration, onCheckIn, onCheckOut }: MainMenuProps) => {
  const menuItems = [
    {
      id: 'face-registration',
      title: 'Đăng ký khuôn mặt',
      subtitle: 'Đăng ký khuôn mặt mới',
      icon: '👤',
      color: '#007AFF',
      action: onFaceRegistration
    },
    {
      id: 'check-in',
      title: 'Check-in',
      subtitle: 'Chấm công vào',
      icon: '⏰',
      color: '#FF3B30',
      action: onCheckIn
    },
    {
      id: 'check-out',
      title: 'Check-out',
      subtitle: 'Chấm công ra',
      icon: '🚪',
      color: '#8E8E93',
      action: onCheckOut
    }
  ];

  return (
    <div className={styles.mainMenu}>
      <div className={styles.header}>
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className={styles.employeeTitle}
        >
          Nhân viên {employee.id}
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className={styles.employeeId}
        >
          ID: {employee.id}
        </motion.p>
      </div>

      <div className={styles.menuItems}>
        {menuItems.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={styles.menuItem}
            onClick={item.action}
          >
            <div className={styles.menuItemContent}>
              <div 
                className={styles.menuItemIcon}
                style={{ backgroundColor: item.color }}
              >
                {item.icon}
              </div>
              <div className={styles.menuItemText}>
                <h3 className={styles.menuItemTitle}>{item.title}</h3>
                <p className={styles.menuItemSubtitle}>{item.subtitle}</p>
              </div>
              <div className={styles.menuItemArrow}>
                →
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        className={styles.instruction}
      >
        Chọn chức năng bạn muốn thực hiện
      </motion.p>
    </div>
  );
};
