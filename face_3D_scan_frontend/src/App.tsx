import { useState, useEffect } from 'react';
import { MainMenu } from './components/MainMenu';
import { FaceScanScreen } from './components/FaceScanScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { useQueryParams } from './hooks/useQueryParams';
import { apiService } from './services/api';
import type { Employee } from './types';
import './App.css';

function App() {
  const { getEmployeeId } = useQueryParams();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [currentAction, setCurrentAction] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('');
  const [processingSubMessage, setProcessingSubMessage] = useState('');

  useEffect(() => {
    const employeeId = getEmployeeId();
    if (employeeId) {
      loadEmployeeInfo(employeeId);
    } else {
      setIsLoading(false);
    }
  }, [getEmployeeId]);

  const loadEmployeeInfo = (employeeId: string) => {
    // Simple fallback - just use the employee ID
    setEmployee({ id: employeeId });
    setIsLoading(false);
  };

  const handleFaceRegistration = () => {
    setCurrentAction('face-registration');
  };

  const handleCheckIn = () => {
    setCurrentAction('checkin');
  };

  const handleCheckOut = () => {
    setCurrentAction('checkout');
  };

  const handleScanComplete = async (videoBlob: Blob) => {
    if (!employee) return;

    // Save current action before clearing it
    const action = currentAction;

    // Show loading screen
    setIsProcessing(true);
    setCurrentAction(null);

    try {
      let response;
      let actionMessage = '';
      
      if (action === 'face-registration') {
        setProcessingMessage('Đang đăng ký khuôn mặt...');
        setProcessingSubMessage('Hệ thống đang xử lý video và tạo dữ liệu sinh trắc học');
        actionMessage = 'Đăng ký khuôn mặt';
        
        response = await apiService.registerFace({
          employeeId: employee.id,
          videoBlob,
        });
      }

      // Show success message
      if (response?.success) {
        setProcessingMessage(`${actionMessage} thành công!`);
        setProcessingSubMessage(response.message || 'Hoàn tất thành công');
        
        // Keep loading screen for 2 seconds to show success message
        setTimeout(() => {
          setIsProcessing(false);
          setProcessingMessage('');
          setProcessingSubMessage('');
        }, 2000);
      } else {
        setProcessingMessage(`${actionMessage} thất bại`);
        setProcessingSubMessage(response?.error || 'Đã xảy ra lỗi');
        
        // Keep loading screen for 3 seconds to show error message
        setTimeout(() => {
          setIsProcessing(false);
          setProcessingMessage('');
          setProcessingSubMessage('');
        }, 3000);
      }
    } catch (error) {
      console.error('Error processing video:', error);
      setProcessingMessage('Đã xảy ra lỗi');
      setProcessingSubMessage('Không thể xử lý video. Vui lòng thử lại.');
      
      // Keep loading screen for 3 seconds to show error message
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingMessage('');
        setProcessingSubMessage('');
      }, 3000);
    }
  };

  const handleCheckInOutComplete = async (result: any) => {
    if (!employee) return;

    // Show loading screen
    setIsProcessing(true);
    setCurrentAction(null);

    try {
      const actionMessage = result.action === 'checkin' ? 'Check-in' : 'Check-out';
      
      if (result.match) {
        setProcessingMessage(`${actionMessage} thành công!`);
        setProcessingSubMessage(`Độ tương đồng: ${(result.similarity * 100).toFixed(1)}%`);
      } else {
        setProcessingMessage(`${actionMessage} thất bại`);
        setProcessingSubMessage(`Độ tương đồng: ${(result.similarity * 100).toFixed(1)}% (cần >= 75%)`);
      }
      
      // Keep loading screen for 3 seconds to show result
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingMessage('');
        setProcessingSubMessage('');
      }, 3000);
    } catch (error) {
      console.error('Error processing result:', error);
      setProcessingMessage('Đã xảy ra lỗi');
      setProcessingSubMessage('Không thể xử lý kết quả. Vui lòng thử lại.');
      
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingMessage('');
        setProcessingSubMessage('');
      }, 3000);
    }
  };

  const handleScanCancel = () => {
    setCurrentAction(null);
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Đang tải...</p>
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="error-screen">
        <h1>Yêu cầu mã nhân viên</h1>
        <p>Vui lòng cung cấp mã nhân viên trong tham số URL.</p>
        <p>Ví dụ: ?id=E001</p>
      </div>
    );
  }

  if (isProcessing) {
    return (
      <LoadingScreen
        message={processingMessage}
        subMessage={processingSubMessage}
      />
    );
  }

  if (currentAction) {
    const mode = currentAction === 'face-registration' ? 'register' : currentAction as 'checkin' | 'checkout';
    return (
      <FaceScanScreen
        employeeId={employee.id}
        mode={mode}
        onComplete={currentAction === 'face-registration' ? handleScanComplete : handleCheckInOutComplete}
        onCancel={handleScanCancel}
      />
    );
  }

  return (
    <MainMenu
      employee={employee}
      onFaceRegistration={handleFaceRegistration}
      onCheckIn={handleCheckIn}
      onCheckOut={handleCheckOut}
    />
  );
}

export default App;
