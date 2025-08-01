# bipedal_test_simulation.py
# 간단한 PyBullet 기반 2D 이족 보행 로봇 시뮬레이션 예제

import pybullet as p
import pybullet_data
import time
import math

# 1. 시뮬레이터 초기화 및 중력 설정
p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.resetSimulation()
p.setGravity(0, 0, -9.81)

# 2. 바닥 로드
plane_id = p.loadURDF("plane.urdf")

# 3. 이족 보행 로봇 모델 생성 함수
def create_biped(base_position=[0,0,0.5]):
    # 골반(pelvis) 프레임
    pelvis_coll = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.1,0.05,0.02])
    pelvis_vis  = p.createVisualShape(p.GEOM_BOX,   halfExtents=[0.1,0.05,0.02], rgbaColor=[0.7,0.7,0.7,1])

    # 허벅지(thigh)와 종아리(shin) 캡슐
    thigh_coll = p.createCollisionShape(p.GEOM_CAPSULE, radius=0.03, height=0.3)
    shin_coll  = p.createCollisionShape(p.GEOM_CAPSULE, radius=0.025, height=0.3)
    thigh_vis  = p.createVisualShape(p.GEOM_CAPSULE, radius=0.03, length=0.3, rgbaColor=[0,0,1,1])
    shin_vis   = p.createVisualShape(p.GEOM_CAPSULE, radius=0.025, length=0.3, rgbaColor=[1,0,0,1])

    # 링크 매개변수
    masses = [1, 0.5, 1, 0.5]
    col_shapes = [thigh_coll, shin_coll, thigh_coll, shin_coll]
    vis_shapes = [thigh_vis,  shin_vis,  thigh_vis,  shin_vis]
    link_positions = [[0.1,0,-0.02], [0,0,-0.15], [-0.1,0,-0.02], [0,0,-0.15]]
    joint_axes = [[1,0,0]] * 4
    joint_types = [p.JOINT_REVOLUTE] * 4
    parent_indices = [0, 1, 0, 3]

    biped = p.createMultiBody(
        baseMass=1,
        baseCollisionShapeIndex=pelvis_coll,
        baseVisualShapeIndex=pelvis_vis,
        basePosition=base_position,
        linkMasses=masses,
        linkCollisionShapeIndices=col_shapes,
        linkVisualShapeIndices=vis_shapes,
        linkPositions=link_positions,
        linkOrientations=[[0,0,0,1]]*4,
        linkInertialFramePositions=[[0,0,0]]*4,
        linkInertialFrameOrientations=[[0,0,0,1]]*4,
        linkParentIndices=parent_indices,
        linkJointTypes=joint_types,
        linkJointAxis=joint_axes
    )
    return biped

# 로봇 생성
biped_id = create_biped()

# 4. 제어 파라미터 설정
kp = 100  # 비례 이득
kd = 2    # 미분 이득

# 5. 단순 보행 궤적 함수 (사인파 기반)
def gait_angle(step, joint_index):
    # 힙(joint_index 0,2) vs 무릎(joint_index 1,3)
    if joint_index % 2 == 0:
        return 0.3 * math.sin(step)
    else:
        return 0.5 * math.sin(step + math.pi/2)

# 6. 시뮬레이션 루프
step = 0.0
time_step = 1./240.
p.setRealTimeSimulation(0)  # 실시간 모드 해제, 수동으로 한 스텝씩 진행
while p.isConnected():
    p.stepSimulation()
    time.sleep(time_step)

    # 각 관절에 토크 제어
    for j in range(p.getNumJoints(biped_id)):
        pos, vel, _, _ = p.getJointState(biped_id, j)
        target = gait_angle(step, j)
        torque = kp * (target - pos) - kd * vel
        p.setJointMotorControl2(
            bodyIndex=biped_id,
            jointIndex=j,
            controlMode=p.TORQUE_CONTROL,
            force=torque
        )

    step += 0.05

p.disconnect()

# 사용법:
# 1) pip install pybullet
# 2) python bipedal_test_simulation.py
