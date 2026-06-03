--[[
================================================================================
Cartographer 2D SLAM 配置文件 (Lua)
--------------------------------------------------------------------------------
文件位置: src/mowen_cartographer/config/mowen_lds_2d.lua
适用场景: 2D 激光雷达建图，无 IMU，纯激光+里程计
机器类型: Mecanum 全向轮小车 (mowen)
================================================================================
主要配置项分类:
  1. 坐标系 (frames)      —— map/odom/base_link 的 TF 关系
  2. 传感器 (sensors)     —— 激光参数、发布周期
  3. Trajectory Builder   —— 扫描匹配、运动滤波、子图构建
  4. Pose Graph           —— 回环检测、全局优化
================================================================================
真实参数文档: https://google-cartographer-ros.readthedocs.io/
--]]

-- 引入 Cartographer 默认配置定义
include "map_builder.lua"
include "trajectory_builder.lua"

options={
    -- =========================================================================
    -- 1. 核心模块选择
    -- =========================================================================
    map_builder = MAP_BUILDER,                          -- 使用 2D 地图构建器
    trajectory_builder = TRAJECTORY_BUILDER,            -- 使用 2D 轨迹构建器
    -- =========================================================================
    -- 2. 坐标系配置 (TF 树)
    -- =========================================================================
    map_frame = "map",                                  -- 全局地图坐标系（SLAM 发布）
    tracking_frame = "base_link",                       -- 跟踪坐标系（机器人本体）
                                                        --   Cartographer 追踪 base_link 的运动
    published_frame = "odom",                           -- 对外发布的坐标系名
                                                        --   Cartographer 发布 map→odom 的 TF
    odom_frame = "odom",                                -- 里程计坐标系名
                                                        --   理解: TF 树为 map → odom → base_link
                                                        --        Cartographer 发布 map→odom
                                                        --        里程计发布 odom→base_link
    provide_odom_frame = false,                         -- 不提供 odom 帧（由 Gazebo/里程计节点提供）
    publish_frame_projected_to_2d = true,               -- 将 3D 位姿投影到 2D 平面再发布 TF
    use_odometry = true,                                -- 使用里程计数据

    -- =========================================================================
    -- 3. 传感器配置
    -- =========================================================================
    use_nav_sat = false,                                -- 不使用 GPS
    use_landmarks = false,                              -- 不使用路标
    num_laser_scans = 1,                                -- 激光雷达数量: 1个
    num_multi_echo_laser_scans = 0,                     -- 多回波激光: 0
    num_subdivisions_per_laser_scan = 1,                -- 每次扫描细分为1段（不拆分）
    num_point_clouds = 0,                               -- 不使用点云

    -- =========================================================================
    -- 4. 数据采集与发布周期
    -- =========================================================================
    -- lookup_transform_timeout_sec: 等待TF变换的超时（秒）
    --    激光数据到达时，需要等到对应的 odom→base_link TF。超过此时间则丢弃该数据。
    lookup_transform_timeout_sec = 0.2,
    -- submap_publish_period_sec: 子图发布间隔（秒）
    --    值越小，Rviz 中地图更新越频繁。0.3 = 每秒发布约3次。
    submap_publish_period_sec = 0.3,
    -- pose_publish_period_sec: 机器人位姿发布间隔（秒）
    --    5e-3 = 0.005秒 = 200Hz，高频发布以保证导航的 TF 流畅度
    pose_publish_period_sec = 5e-3,
    -- trajectory_publish_period_sec: 轨迹发布间隔（秒）
    --    用于Rviz可视化机器人的运动轨迹
    trajectory_publish_period_sec = 30e-3,

    -- =========================================================================
    -- 5. 采样比率（控制数据流量的"采样率"）
    --    =1.0 表示每条数据都处理，较低值表示丢弃部分数据
    -- =========================================================================
    rangefinder_sampling_ratio = 1.,                    -- 激光全部处理
    odometry_sampling_ratio = 1.,                       -- 里程计全部处理
    fixed_frame_pose_sampling_ratio = 1.,               -- 固定帧位姿全部处理
    imu_sampling_ratio = 1.,                            -- IMU全部处理（即使不使用）
    landmarks_sampling_ratio = 1.,                      -- 路标全部处理
}

-- =============================================================================
-- 6. Trajectory Builder (轨迹构建器 / 前端)
--    负责: 激光扫描匹配 → 构建子图(submap)
-- =============================================================================
MAP_BUILDER.use_trajectory_builder_2d = true            -- 使用 2D 轨迹构建器

-- -------- 激光距离过滤 --------------------------------------
-- min_range: 最小有效距离（米），小于此值的点被丢弃
--    mowen 机器人自身尺寸约 0.16m(-0.26~+0.16)，激光装在前部x=0.1处
--    0.25 确保过滤掉扫到自身的点（轮子、车身边缘）
TRAJECTORY_BUILDER_2D.min_range = 0.25
-- max_range: 最大有效距离（米），大于此值的点被丢弃
--    3.5 匹配 Gazebo 中激光的最大距离
TRAJECTORY_BUILDER_2D.max_range = 3.5
-- missing_data_ray_length: 超量程时"假射线"长度（米）
--    激光发射但没收到回波（超出量程或物体太远），插入一条此长度的假射线
--    通常设为 max_range 的 80-90%
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.0

-- -------- IMU -----------------------------------------------
TRAJECTORY_BUILDER_2D.use_imu_data = false              -- 不使用IMU数据

-- -------- 扫描匹配 ------------------------------------------
-- use_online_correlative_scan_matching:
--   true  → 使用实时CSM（相关扫描匹配），精度更高但计算量大
--   false → 只用里程计+IMU推算，速度快但易漂移
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

-- -------- 运动滤波器 ----------------------------------------
-- 作用: 只有机器人运动超过阈值，才插入新的激光数据。过滤静止时的重复扫描。
-- max_angle_radians: 角度变化阈值（弧度），超过才处理新数据
--   math.rad(0.1) ≈ 5.7°，较小的阈值意味着更频繁地插入数据，建图更精细
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.1)

-- =============================================================================
-- 7. Pose Graph (位姿图 / 后端)
--    负责: 回环检测 → 全局优化 → 修正累积误差
-- =============================================================================
-- min_score: 回环检测的最低匹配分数
--   0.65 是室内环境的常用值。分数越高，回环越可靠（但可能漏检）
POSE_GRAPH.constraint_builder.min_score = 0.65
-- global_localization_min_score: 全局重定位的最低匹配分数
--   比回环检测更严格(0.7)，因为全局重定位错误会导致地图撕裂
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7

return options
