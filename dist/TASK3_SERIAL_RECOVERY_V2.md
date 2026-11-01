# 旧批次恢复入口 v2：修复作业状态查询

当前错误发生在核验旧作业38349的阶段，尚未提交新恢复作业。v2不再按已退出队列的Job ID请求squeue，而是读取当前用户队列，用数组基础ID匹配，并由sacct的JobID字段核验历史普通/数组作业及退出码。真实查询错误保留stderr并停止，找不到历史记录也不会假定完成。

只上传dist/task3_serial_recovery_v2.py到原incoming/task3_v1_20261022/目录，不修改旧release、配置或1200份结果。当前失败尝试没有创建恢复状态，因此首次启动不加--resume；如果原先已有serial_recovery_state.json，保留文件并先核实来源，不删状态或改哈希。

在已激活myenv的集群终端逐行执行：

```bash
cd /public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task3_v1_20261022
python -B task3_serial_recovery_v2.py --release /public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task3_v1_20261022 --config cluster_config.json --dry-run
nohup python -B task3_serial_recovery_v2.py --release /public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task3_v1_20261022 --config cluster_config.json > serial_recovery_v2.log 2>&1 < /dev/null &
```

查看serial_recovery_v2.log、squeue，以及原结果目录的serial_recovery_state.json。科学结果和完整性检查文件仍在原目录；原controller_state.json保留blocked。v2成功启动后如中断，核实原因后对同一v2脚本加--resume，不重新用旧脚本或旧控制器。

验证：11项离线调度/恢复测试通过，Python3.9语法及独立CLI参数解析通过，未连接集群或提交作业。原ZIP和锁修复ZIP均未覆盖。

官方字段依据：https://slurm.schedmd.com/squeue.html 与 https://slurm.schedmd.com/sacct.html。
