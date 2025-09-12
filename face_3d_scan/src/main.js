import { faceAPI } from './face-api.js';
import './style.css';

// Set the HTML content
document.querySelector('#app').innerHTML = `
  <div class="container">
    <header>
      <h1>Hệ thống nhận diện khuôn mặt 3D</h1>
      <nav>
        <button class="tab-btn active" data-tab="register">Đăng ký</button>
        <button class="tab-btn" data-tab="checkin">Check-in</button>
        <button class="tab-btn" data-tab="checkout">Check-out</button>
      </nav>
    </header>

    <main>
      <!-- Register Tab -->
      <div id="register" class="tab-content active">
        <h2>Đăng ký nhận diện khuôn mặt</h2>
        <div class="form-group">
          <label for="employeeId">Mã nhân viên:</label>
          <input type="text" id="employeeId" placeholder="Nhập mã nhân viên">
        </div>
        <div class="video-container">
          <video id="registerVideo" autoplay muted></video>
          <div class="overlay">
            <div class="face-guide"></div>
          </div>
        </div>
        <div class="controls">
          <button id="startRegister">Bắt đầu ghi hình (10s)</button>
          <button id="stopRegister" disabled>Dừng</button>
          <button id="upload3x4">Tải ảnh 3x4</button>
          <input type="file" id="photo3x4" accept="image/*" style="display: none;">
        </div>
        <div class="status" id="registerStatus"></div>
      </div>

      <!-- Check-in Tab -->
      <div id="checkin" class="tab-content">
        <h2>Check-in</h2>
        <div class="video-container">
          <video id="checkinVideo" autoplay muted></video>
          <div class="overlay">
            <div class="face-guide"></div>
          </div>
        </div>
        <div class="controls">
          <button id="startCheckin">Bắt đầu ghi hình (3s)</button>
          <button id="stopCheckin" disabled>Dừng</button>
        </div>
        <div class="status" id="checkinStatus"></div>
      </div>

      <!-- Check-out Tab -->
      <div id="checkout" class="tab-content">
        <h2>Check-out</h2>
        <div class="video-container">
          <video id="checkoutVideo" autoplay muted></video>
          <div class="overlay">
            <div class="face-guide"></div>
          </div>
        </div>
        <div class="controls">
          <button id="startCheckout">Bắt đầu ghi hình (3s)</button>
          <button id="stopCheckout" disabled>Dừng</button>
        </div>
        <div class="status" id="checkoutStatus"></div>
      </div>
    </main>
  </div>
`;

// DOM Elements
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Video elements
const registerVideo = document.getElementById('registerVideo');
const checkinVideo = document.getElementById('checkinVideo');
const checkoutVideo = document.getElementById('checkoutVideo');

// Buttons
const startRegisterBtn = document.getElementById('startRegister');
const stopRegisterBtn = document.getElementById('stopRegister');
const upload3x4Btn = document.getElementById('upload3x4');
const photo3x4Input = document.getElementById('photo3x4');
const startCheckinBtn = document.getElementById('startCheckin');
const stopCheckinBtn = document.getElementById('stopCheckin');
const startCheckoutBtn = document.getElementById('startCheckout');
const stopCheckoutBtn = document.getElementById('stopCheckout');

// Status elements
const registerStatus = document.getElementById('registerStatus');
const checkinStatus = document.getElementById('checkinStatus');
const checkoutStatus = document.getElementById('checkoutStatus');

// Employee ID input
const employeeIdInput = document.getElementById('employeeId');

// Current active tab
let currentTab = 'register';
let currentStream = null;

// Tab switching
function switchTab(tabId) {
  // Hide all tab contents
  tabContents.forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Deactivate all tab buttons
  tabButtons.forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Show the selected tab content
  document.getElementById(tabId).classList.add('active');
  
  // Activate the clicked tab button
  document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
  
  // Store current tab
  currentTab = tabId;
  
  // Initialize camera for the active tab
  initCameraForTab(tabId);
}

// Initialize camera for the active tab
async function initCameraForTab(tabId) {
  // Stop any existing camera stream
  if (currentStream) {
    currentStream.getTracks().forEach(track => track.stop());
    currentStream = null;
  }

  try {
    let videoElement;
    
    switch(tabId) {
      case 'register':
        videoElement = registerVideo;
        break;
      case 'checkin':
        videoElement = checkinVideo;
        break;
      case 'checkout':
        videoElement = checkoutVideo;
        break;
      default:
        return;
    }
    
    // Initialize camera
    currentStream = await faceAPI.initCamera(videoElement, 'user');
    
  } catch (error) {
    console.error('Error initializing camera:', error);
    showStatus('error', `Lỗi khởi tạo camera: ${error.message}`, tabId);
  }
}

// Show status message
function showStatus(type, message, tab) {
  let statusElement;
  
  switch(tab) {
    case 'register':
      statusElement = registerStatus;
      break;
    case 'checkin':
      statusElement = checkinStatus;
      break;
    case 'checkout':
      statusElement = checkoutStatus;
      break;
    default:
      return;
  }
  
  statusElement.textContent = message;
  statusElement.className = 'status';
  statusElement.classList.add(type);
  
  // Auto-hide success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      if (statusElement.textContent === message) {
        statusElement.textContent = '';
        statusElement.className = 'status';
      }
    }, 5000);
  }
}

// Start registration recording
async function startRegistration() {
  if (!employeeIdInput.value.trim()) {
    showStatus('error', 'Vui lòng nhập mã nhân viên', 'register');
    return;
  }
  
  startRegisterBtn.disabled = true;
  stopRegisterBtn.disabled = false;
  upload3x4Btn.disabled = true;
  
  // Start recording for 10 seconds
  faceAPI.startRecording(registerVideo, 
    (time) => {
      // Update UI with remaining time
      const remaining = 10 - time;
      if (remaining > 0) {
        showStatus('info', `Đang ghi hình... ${remaining} giây còn lại`, 'register');
      }
    },
    async (blob) => {
      // Recording stopped
      startRegisterBtn.disabled = false;
      stopRegisterBtn.disabled = true;
      upload3x4Btn.disabled = false;
      
      try {
        showStatus('info', 'Đang xử lý video...', 'register');
        
        // Send video to server for registration
        const response = await faceAPI.registerEmployee(employeeIdInput.value, blob);
        
        if (response.success) {
          showStatus('success', 'Đăng ký khuôn mặt thành công!', 'register');
        } else {
          showStatus('error', response.message || 'Có lỗi xảy ra khi đăng ký', 'register');
        }
      } catch (error) {
        console.error('Registration error:', error);
        showStatus('error', `Lỗi: ${error.message}`, 'register');
      }
    }
  );
  
  // Auto-stop after 10 seconds
  setTimeout(() => {
    if (faceAPI.mediaRecorder && faceAPI.mediaRecorder.state === 'recording') {
      faceAPI.stopRecording();
    }
  }, 10000);
}

// Start check-in recording
async function startCheckIn() {
  startCheckinBtn.disabled = true;
  stopCheckinBtn.disabled = false;
  
  // Start recording for 3 seconds
  faceAPI.startRecording(checkinVideo, 
    (time) => {
      // Update UI with remaining time
      const remaining = 3 - time;
      if (remaining > 0) {
        showStatus('info', `Đang ghi hình... ${remaining} giây còn lại`, 'checkin');
      }
    },
    async (blob) => {
      // Recording stopped
      startCheckinBtn.disabled = false;
      stopCheckinBtn.disabled = true;
      
      try {
        showStatus('info', 'Đang xác thực...', 'checkin');
        
        // Send video to server for check-in
        const response = await faceAPI.checkIn(blob);
        
        if (response.match) {
          showStatus('success', `Check-in thành công! Nhân viên: ${response.employee_id} (Độ chính xác: ${(response.similarity * 100).toFixed(2)}%)`, 'checkin');
        } else {
          showStatus('error', response.message || 'Không nhận diện được khuôn mặt', 'checkin');
        }
      } catch (error) {
        console.error('Check-in error:', error);
        showStatus('error', `Lỗi: ${error.message}`, 'checkin');
      }
    }
  );
  
  // Auto-stop after 3 seconds
  setTimeout(() => {
    if (faceAPI.mediaRecorder && faceAPI.mediaRecorder.state === 'recording') {
      faceAPI.stopRecording();
    }
  }, 3000);
}

// Start check-out recording
async function startCheckOut() {
  startCheckoutBtn.disabled = true;
  stopCheckoutBtn.disabled = false;
  
  // Start recording for 3 seconds
  faceAPI.startRecording(checkoutVideo, 
    (time) => {
      // Update UI with remaining time
      const remaining = 3 - time;
      if (remaining > 0) {
        showStatus('info', `Đang ghi hình... ${remaining} giây còn lại`, 'checkout');
      }
    },
    async (blob) => {
      // Recording stopped
      startCheckoutBtn.disabled = false;
      stopCheckoutBtn.disabled = true;
      
      try {
        showStatus('info', 'Đang xác thực...', 'checkout');
        
        // Send video to server for check-out
        const response = await faceAPI.checkOut(blob);
        
        if (response.match) {
          showStatus('success', `Check-out thành công! Nhân viên: ${response.employee_id} (Độ chính xác: ${(response.similarity * 100).toFixed(2)}%)`, 'checkout');
        } else {
          showStatus('error', response.message || 'Không nhận diện được khuôn mặt', 'checkout');
        }
      } catch (error) {
        console.error('Check-out error:', error);
        showStatus('error', `Lỗi: ${error.message}`, 'checkout');
      }
    }
  );
  
  // Auto-stop after 3 seconds
  setTimeout(() => {
    if (faceAPI.mediaRecorder && faceAPI.mediaRecorder.state === 'recording') {
      faceAPI.stopRecording();
    }
  }, 3000);
}

// Handle 3x4 photo upload
async function handle3x4Upload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const employeeId = employeeIdInput.value.trim();
  if (!employeeId) {
    showStatus('error', 'Vui lòng nhập mã nhân viên trước', 'register');
    return;
  }
  
  try {
    showStatus('info', 'Đang tải lên ảnh 3x4...', 'register');
    
    // Upload the photo
    const response = await faceAPI.upload3x4Photo(employeeId, file);
    
    if (response.success) {
      showStatus('success', 'Tải lên ảnh 3x4 thành công!', 'register');
    } else {
      showStatus('error', response.message || 'Có lỗi xảy ra khi tải lên ảnh', 'register');
    }
  } catch (error) {
    console.error('Upload error:', error);
    showStatus('error', `Lỗi: ${error.message}`, 'register');
  }
  
  // Reset file input
  event.target.value = '';
}

// Event Listeners
function initEventListeners() {
  // Tab switching
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const tabId = button.getAttribute('data-tab');
      switchTab(tabId);
    });
  });
  
  // Register tab
  startRegisterBtn.addEventListener('click', startRegistration);
  stopRegisterBtn.addEventListener('click', () => faceAPI.stopRecording());
  upload3x4Btn.addEventListener('click', () => photo3x4Input.click());
  photo3x4Input.addEventListener('change', handle3x4Upload);
  
  // Check-in tab
  startCheckinBtn.addEventListener('click', startCheckIn);
  stopCheckinBtn.addEventListener('click', () => faceAPI.stopRecording());
  
  // Check-out tab
  startCheckoutBtn.addEventListener('click', startCheckOut);
  stopCheckoutBtn.addEventListener('click', () => faceAPI.stopRecording());
}

// Initialize the application
async function initApp() {
  // Initialize event listeners
  initEventListeners();
  
  // Start with the register tab
  switchTab('register');
  
  // Check for camera access
  try {
    await navigator.mediaDevices.getUserMedia({ video: true });
  } catch (error) {
    showStatus('error', 'Không thể truy cập camera. Vui lòng cấp quyền truy cập camera.', 'register');
  }
}

// Start the application when the DOM is fully loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

document.querySelector('#app').innerHTML = `
  <div>
    <a href="https://vite.dev" target="_blank">
      <img src="/vite.svg" class="logo" alt="Vite logo" />
    </a>
    <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript" target="_blank">
      <img src="./javascript.svg" class="logo vanilla" alt="JavaScript logo" />
    </a>
    <h1>Hello Vite!</h1>
    <div class="card">
      <button id="counter" type="button"></button>
    </div>
    <div class="tabs">
      <button class="tab-btn active" data-tab="register">Đăng ký</button>
      <button class="tab-btn" data-tab="checkin">Check-in</button>
      <button class="tab-btn" data-tab="checkout">Check-out</button>
    </div>
    <div class="tab-content active" id="register">
      <h2>Đăng ký khuôn mặt</h2>
      <video id="registerVideo" width="640" height="480"></video>
      <button id="startRegister">Bắt đầu ghi hình</button>
      <button id="stopRegister">Dừng ghi hình</button>
      <button id="upload3x4">Tải lên ảnh 3x4</button>
      <input type="file" id="photo3x4" style="display: none;">
      <div id="registerStatus" class="status"></div>
    </div>
    <div class="tab-content" id="checkin">
      <h2>Check-in</h2>
      <video id="checkinVideo" width="640" height="480"></video>
      <button id="startCheckin">Bắt đầu ghi hình</button>
      <button id="stopCheckin">Dừng ghi hình</button>
      <div id="checkinStatus" class="status"></div>
    </div>
    <div class="tab-content" id="checkout">
      <h2>Check-out</h2>
      <video id="checkoutVideo" width="640" height="480"></video>
      <button id="startCheckout">Bắt đầu ghi hình</button>
      <button id="stopCheckout">Dừng ghi hình</button>
      <div id="checkoutStatus" class="status"></div>
    </div>
    <input type="text" id="employeeId" placeholder="Nhập mã nhân viên">
    <p class="read-the-docs">
      Click on the Vite logo to learn more
    </p>
  </div>
`;
