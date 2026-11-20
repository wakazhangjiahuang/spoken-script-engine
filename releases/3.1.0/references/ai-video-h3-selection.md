# H3 Reference Selection与素材绑定

P01只锁人物身份；P02只锁场景环境；二者都不是首帧。A01是可选且必须授权的声音参考；未选择A01时，Prompt必须删除全部<Audio 1>定义。P03+为单镜头专用参考。R类素材是屏录、采访、产品/项目实拍和真实证据，默认不传H3，只在后期插入。

S1系列主讲数字人可按授权参考生成；S2真实采访者默认真人拍摄。未经肖像、声音和商业用途明确授权，不生成其数字分身。真实UI、测试数据、采访和客户证据不得让H3重绘。

每镜Prompt必须包含subject_definitions、summary、retention_analysis、detailed_description、overall_soundscape、non_diegetic_music，并写清构图、机位、动作、运镜、时间线、逐字台词和负面约束。