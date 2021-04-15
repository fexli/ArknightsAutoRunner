# <-ArkMap
# OThER MAP CONDItION
# 喧闹法则        - CB - Y
# 骑兵与猎人       - GT - N
# 火蓝之心        - OF - N
# 战地秘闻        - SW - N
# 洪炉示岁        - AF - N
# 午间逸话        - SA - N
# 生于黑夜        - DM - Y
# 乌萨斯的孩子们   - SV - N
# 沃伦姆德的薄暮   - TW - N
# 密林悍将归来     - RI - N
# 刻俄柏的灰蕈迷境 - ISW - N
# 踏寻往昔之风     - FA - N
# 玛莉娅·临光     - MN - N
# 孤岛风云        - NB - Y
# 此地之外        - BH - N
# 画中人          - WR - Y
# 源氏尘行动       - OD - y
# 活动地图标识总览
ACTIVITY_MAP = ['CB', 'GT', 'OF', 'SW', 'AF', 'SA', 'DM', 'SV', 'TW', 'RI', 'ISW', 'FA', 'MN', "NB", 'BH', 'WR', 'OD',
                'DM']
# 常规地图标识总览
NORMAL_MAP = ['AP', 'CE', 'LS', 'CA', 'SK']
# 可识别的位置数据总览（在ArkMap中分配了不同识别地图的行动方法）
ArkMap_RECO = ['map_atk', 'main', 'map_main', 'map_exterm', 'map_ep', 'map_mat', 'map_CB', 'map_MB', 'map_WR', 'map_OD',
               'map_DM']
# 已经完成行动方法的地图（由于没复刻以及懒得做等原因不是很全）
ArkMap_ACTIVITY = ['map_CB', 'map_MB', 'map_WR', 'map_OD', 'map_DM']

# 主线关卡分类 主线视图(873,385,145,64) 阶段视图左侧名字
ArkMap_MainStage = {
    'epstage1': [0, 1, 2, 3],
    'epstage2': [4, 5, 6, 7, 8],
}
# ArkMap->

# <-ArkAutoRunner
# 剿灭作战不同剿灭位置数据（在初始进入位置有效）
EXTER_CLICK_DATA = {
    "北原冰封废城": [(640, 340), (270, 384)],
    "切尔诺伯格": [(640, 340), (948, 402)],
    "龙门外环": [(983, 565), (478, 454)],
    "龙门市区": [(983, 565), (807, 241)],
    "大骑士领郊外": [(88, 528), (523, 371)],
    "废弃矿区": [(640, 340), (572, 232)]
}
MIN_ENABLE_EXTER_ATK_CAMP_NUM = 100  # 最小允许开启剿灭作战的合成玉差量(合成玉获取上限-当前合成玉数量)
# ArkAutoRunner->

# <-Character.py

# Character.py->

# Penguin Stats Data
PENGUIN_STATS_ID = '31444514'
