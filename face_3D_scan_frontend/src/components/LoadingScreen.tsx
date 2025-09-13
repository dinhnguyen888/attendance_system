import { motion } from 'framer-motion';
import styles from './LoadingScreen.module.css';

interface LoadingScreenProps {
  message: string;
  subMessage?: string;
}

export const LoadingScreen = ({ message, subMessage }: LoadingScreenProps) => {
  return (
    <div className={styles.loadingScreen}>
      <div className={styles.loadingContainer}>
        {/* Animated spinner */}
        <motion.div
          className={styles.spinner}
          animate={{ rotate: 360 }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "linear"
          }}
        >
          <div className={styles.spinnerInner} />
        </motion.div>

        {/* Progress dots */}
        <div className={styles.progressDots}>
          <motion.div
            className={styles.dot}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5]
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: 0
            }}
          />
          <motion.div
            className={styles.dot}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5]
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: 0.2
            }}
          />
          <motion.div
            className={styles.dot}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5]
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: 0.4
            }}
          />
        </div>

        {/* Main message */}
        <motion.h2
          className={styles.mainMessage}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {message}
        </motion.h2>

        {/* Sub message */}
        {subMessage && (
          <motion.p
            className={styles.subMessage}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            {subMessage}
          </motion.p>
        )}

        {/* Processing steps */}
        <div className={styles.processingSteps}>
          <motion.div
            className={styles.step}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
          >
            <div className={styles.stepIcon}>📹</div>
            <span>Đang xử lý video...</span>
          </motion.div>
          
          <motion.div
            className={styles.step}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 1.0 }}
          >
            <div className={styles.stepIcon}>🔍</div>
            <span>Trích xuất khuôn mặt...</span>
          </motion.div>
          
          <motion.div
            className={styles.step}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 1.3 }}
          >
            <div className={styles.stepIcon}>🧠</div>
            <span>Phân tích dữ liệu...</span>
          </motion.div>
        </div>
      </div>
    </div>
  );
};