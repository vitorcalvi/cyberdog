import { createSignal, onMount, onCleanup, Component } from "solid-js";

// ROSLib types
declare global {
  interface Window {
    ROSLIB: any;
  }
}

type BatteryState = {
  voltage: number;
  percentage: number;
  power_supply_status: number;
};

type ImuState = {
  orientation: { x: number; y: number; z: number; w: number };
  angular_velocity: { x: number; y: number; z: number };
  linear_acceleration: { x: number; y: number; z: number };
};

type JointState = {
  name: string[];
  position: number[];
  velocity: number[];
  effort: number[];
};

type Twist = {
  linear: { x: number; y: number; z: number };
  angular: { x: number; y: number; z: number };
};

const App: Component = () => {
  // Connection state
  const [connected, setConnected] = createSignal(false);
  const [rosUrl] = createSignal("ws://192.168.20.10:9090");
  
  // Robot state
  const [battery, setBattery] = createSignal<BatteryState | null>(null);
  const [imu, setImu] = createSignal<ImuState | null>(null);
  const [joints, setJoints] = createSignal<JointState | null>(null);
  const [cmdVel, setCmdVel] = createSignal<Twist>({ 
    linear: { x: 0, y: 0, z: 0 }, 
    angular: { x: 0, y: 0, z: 0 } 
  });
  const [gaitMode, setGaitMode] = createSignal("trot");
  
  let ros: any = null;
  let cmdVelTopic: any = null;
  let batteryTopic: any = null;
  let imuTopic: any = null;
  let jointTopic: any = null;

  onMount(() => {
    connect();
  });

  onCleanup(() => {
    disconnect();
  });

  const connect = () => {
    try {
      ros = new window.ROSLIB.Ros({ url: rosUrl() });
      
      ros.on("connection", () => {
        console.log("Connected to ROS bridge");
        setConnected(true);
        subscribeTopics();
        setupPublishers();
      });
      
      ros.on("error", (error: any) => {
        console.error("ROS connection error:", error);
        setConnected(false);
      });
      
      ros.on("close", () => {
        console.log("Connection to ROS bridge closed");
        setConnected(false);
      });
    } catch (e) {
      console.error("Failed to create ROS connection:", e);
    }
  };

  const disconnect = () => {
    if (ros) ros.close();
    setConnected(false);
  };

  const subscribeTopics = () => {
    if (!ros) return;

    // Battery state
    batteryTopic = new window.ROSLIB.Topic({
      ros: ros,
      name: "/battery_state",
      messageType: "sensor_msgs/msg/BatteryState"
    });
    batteryTopic.subscribe((msg: any) => setBattery(msg));

    // IMU
    imuTopic = new window.ROSLIB.Topic({
      ros: ros,
      name: "/imu/data",
      messageType: "sensor_msgs/msg/Imu"
    });
    imuTopic.subscribe((msg: any) => setImu(msg));

    // Joint states
    jointTopic = new window.ROSLIB.Topic({
      ros: ros,
      name: "/joint_states",
      messageType: "sensor_msgs/msg/JointState"
    });
    jointTopic.subscribe((msg: any) => setJoints(msg));
  };

  const setupPublishers = () => {
    if (!ros) return;
    
    cmdVelTopic = new window.ROSLIB.Topic({
      ros: ros,
      name: "/cmd_vel",
      messageType: "geometry_msgs/msg/Twist"
    });
    cmdVelTopic.advertise();
  };

  const publishCmdVel = (linear: number, angular: number) => {
    if (!cmdVelTopic || !connected()) return;
    
    const twist = new window.ROSLIB.Message({
      linear: { x: linear, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: angular }
    });
    cmdVelTopic.publish(twist);
    setCmdVel({ 
      linear: { x: linear, y: 0, z: 0 }, 
      angular: { x: 0, y: 0, z: angular } 
    });
  };

  const stopRobot = () => publishCmdVel(0, 0);
  const moveForward = () => publishCmdVel(0.3, 0);
  const moveBackward = () => publishCmdVel(-0.2, 0);
  const turnLeft = () => publishCmdVel(0, 0.5);
  const turnRight = () => publishCmdVel(0, -0.5);

  const getBatteryIcon = () => {
    const pct = battery()?.percentage ?? 0;
    if (pct > 75) return "fa-battery-full";
    if (pct > 50) return "fa-battery-three-quarters";
    if (pct > 25) return "fa-battery-half";
    if (pct > 0) return "fa-battery-quarter";
    return "fa-battery-empty";
  };

  const getBatteryColor = () => {
    const pct = battery()?.percentage ?? 0;
    if (pct > 50) return "#4ade80";
    if (pct > 20) return "#fbbf24";
    return "#f87171";
  };

  const quaternionToEuler = (q: { x: number; y: number; z: number; w: number }) => {
    const sinr_cosp = 2 * (q.w * q.x + q.y * q.z);
    const cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y);
    const roll = Math.atan2(sinr_cosp, cosr_cosp) * 180 / Math.PI;
    
    const sinp = 2 * (q.w * q.y - q.z * q.x);
    const pitch = Math.abs(sinp) >= 1 ? Math.sign(sinp) * 90 : Math.asin(sinp) * 180 / Math.PI;
    
    const siny_cosp = 2 * (q.w * q.z + q.x * q.y);
    const cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z);
    const yaw = Math.atan2(siny_cosp, cosy_cosp) * 180 / Math.PI;
    
    return { roll, pitch, yaw };
  };

  const euler = () => {
    const imuData = imu();
    if (!imuData) return { roll: 0, pitch: 0, yaw: 0 };
    return quaternionToEuler(imuData.orientation);
  };

  const jointLabels: Record<string, string> = {
    "FL_hip": "FL Hip", "FL_thigh": "FL Thigh", "FL_calf": "FL Calf",
    "FR_hip": "FR Hip", "FR_thigh": "FR Thigh", "FR_calf": "FR Calf",
    "RL_hip": "RL Hip", "RL_thigh": "RL Thigh", "RL_calf": "RL Calf",
    "RR_hip": "RR Hip", "RR_thigh": "RR Thigh", "RR_calf": "RR Calf",
  };

  return (
    <div class="dashboard">
      {/* Header */}
      <div class="header">
        <div style="display: flex; align-items: center; gap: 15px;">
          <i class="fa-solid fa-dog" style="font-size: 28px; color: #60a5fa;"></i>
          <h1 style="font-size: 22px;">CyberDog Dashboard</h1>
        </div>
        <div class="connection-status">
          <div class={`status-dot ${connected() ? "connected" : "disconnected"}`}
               style={`background: ${connected() ? "#4ade80" : "#f87171"}`}></div>
          <span>{connected() ? "Connected" : "Disconnected"}</span>
        </div>
      </div>

      {/* Left Panel - Status */}
      <div class="panel">
        <h3 style="margin-bottom: 15px; color: #60a5fa;">Robot Status</h3>
        
        <div class="indicator">
          <i class={`fa-solid ${getBatteryIcon()}`} 
             style={`color: ${getBatteryColor()}`}></i>
          <div>
            <div class="value">{battery() ? `${Math.round(battery()!.percentage * 100)}%` : "---"}</div>
            <div class="label">Battery ({battery() ? `${battery()!.voltage.toFixed(1)}V` : "--- V"})</div>
          </div>
        </div>

        <div class="indicator">
          <i class="fa-solid fa-compass" style="color: #60a5fa;"></i>
          <div>
            <div class="value">{`${euler().yaw.toFixed(1)}°`}</div>
            <div class="label">Yaw</div>
          </div>
        </div>

        <div class="indicator">
          <i class="fa-solid fa-arrows-alt" style="color: #a78bfa;"></i>
          <div>
            <div class="value">{`R:${euler().roll.toFixed(1)}° P:${euler().pitch.toFixed(1)}°`}</div>
            <div class="label">Roll / Pitch</div>
          </div>
        </div>

        <div class="indicator">
          <i class="fa-solid fa-walking" style="color: #34d399;"></i>
          <div>
            <div class="value">{gaitMode().toUpperCase()}</div>
            <div class="label">Gait Mode</div>
          </div>
        </div>

        <h4 style="margin: 20px 0 10px; color: #60a5fa;">Joint States</h4>
        <div class="joint-grid">
          {joints() && joints()!.name.map((name, i) => (
            <div class="joint-item">
              <div class="name">{jointLabels[name] || name}</div>
              <div class="angle">{(joints()!.position[i] * 180 / Math.PI).toFixed(1)}°</div>
            </div>
          ))}
        </div>
      </div>

      {/* Center - Control */}
      <div class="panel control-panel">
        <h3 style="margin-bottom: 15px; color: #60a5fa;">Motion Control</h3>
        
        <div class="velocity-display">
          <h3>Current Velocity</h3>
          <div class="value" style="color: #60a5fa;">
            {cmdVel().linear.x.toFixed(2)} m/s
          </div>
          <div style="opacity: 0.7; margin-top: 5px;">
            Angular: {cmdVel().angular.z.toFixed(2)} rad/s
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px;">
          <div></div>
          <button class="control-btn forward" onClick={moveForward}>
            <i class="fa-solid fa-arrow-up"></i> Forward
          </button>
          <div></div>
          
          <button class="control-btn left" onClick={turnLeft}>
            <i class="fa-solid fa-arrow-left"></i> Left
          </button>
          <button class="control-btn stop" onClick={stopRobot}>
            <i class="fa-solid fa-stop"></i> Stop
          </button>
          <button class="control-btn right" onClick={turnRight}>
            <i class="fa-solid fa-arrow-right"></i> Right
          </button>
          
          <div></div>
          <button class="control-btn backward" onClick={moveBackward}>
            <i class="fa-solid fa-arrow-down"></i> Back
          </button>
          <div></div>
        </div>

        <h4 style="margin: 30px 0 15px; color: #60a5fa;">Gait Selection</h4>
        <div class="gait-selector">
          {["trot", "walk", "pace", "bound"].map(gait => (
            <button 
              class={`gait-btn ${gaitMode() === gait ? "active" : ""}`}
              onClick={() => setGaitMode(gait)}>
              {gait.charAt(0).toUpperCase() + gait.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Right Panel - Info */}
      <div class="panel">
        <h3 style="margin-bottom: 15px; color: #60a5fa;">System Info</h3>
        
        <div class="indicator">
          <i class="fa-solid fa-robot" style="color: #60a5fa;"></i>
          <div>
            <div class="value">CyberDog</div>
            <div class="label">Model</div>
          </div>
        </div>

        <div class="indicator">
          <i class="fa-solid fa-microchip" style="color: #fbbf24;"></i>
          <div>
            <div class="value">NVIDIA Jetson</div>
            <div class="label">Platform</div>
          </div>
        </div>

        <div class="indicator">
          <i class="fa-solid fa-network-wired" style="color: #34d399;"></i>
          <div>
            <div class="value">192.168.20.10</div>
            <div class="label">IP Address</div>
          </div>
        </div>

        <h4 style="margin: 20px 0 10px; color: #60a5fa;">IMU Data</h4>
        <div style="font-size: 12px; opacity: 0.8; line-height: 1.8;">
          <div>Accel: {imu() ? 
            `X:${imu()!.linear_acceleration.x.toFixed(2)} Y:${imu()!.linear_acceleration.y.toFixed(2)} Z:${imu()!.linear_acceleration.z.toFixed(2)}` 
            : "---"}</div>
          <div>Gyro: {imu() ? 
            `X:${imu()!.angular_velocity.x.toFixed(2)} Y:${imu()!.angular_velocity.y.toFixed(2)} Z:${imu()!.angular_velocity.z.toFixed(2)}` 
            : "---"}</div>
        </div>

        <h4 style="margin: 20px 0 10px; color: #60a5fa;">ROS2 Topics</h4>
        <div style="font-size: 11px; opacity: 0.7; line-height: 1.6;">
          <div>/cmd_vel</div>
          <div>/joint_states</div>
          <div>/battery_state</div>
          <div>/imu/data</div>
          <div>/odom</div>
        </div>
      </div>

      {/* Footer */}
      <div class="footer">
        <div style="display: flex; gap: 30px; align-items: center;">
          <span style="opacity: 0.7;">
            <i class="fa-solid fa-code"></i> ROS2 Galactic
          </span>
          <span style="opacity: 0.7;">
            <i class="fa-solid fa-globe"></i> Rosbridge: ws://192.168.20.10:9090
          </span>
          <span style="opacity: 0.7;">
            <i class="fa-brands fa-github"></i> vitorcalvi/cyberdog
          </span>
        </div>
      </div>
    </div>
  );
};

export default App;
