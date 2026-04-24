"""NPC状态管理器 - 定时批量更新NPC对话"""

import asyncio
from datetime import datetime
from typing import Dict, Optional
from batch_generator import get_batch_generator

class NPCStateManager:
    def __init__(self,update_interval:int=30):
        """初始化状态管理器
        
        Args:
            update_interval: 更新间隔(秒),默认30秒
        """
        self.update_interval = update_interval
        self.batch_generator = get_batch_generator()
        # 当前状态
        self.current_dialogues: Dict[str, str] = {}
        self.last_update: Optional[datetime] = None
        self.next_update_time: Optional[datetime] = None
        
        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        
        print(f"📊 NPC状态管理器初始化完成 (更新间隔: {update_interval}秒)")
    async def start(self):
        if self._running:
            print("⚠️  状态管理器已在运行")
            return
        self._running = True
        print("🚀 启动NPC状态自动更新...")
        # 立即执行一次更新
        await self._update_npc_states()
        
        # 启动定时更新任务
        self._update_task = asyncio.create_task(self._auto_update_loop())
    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        print("🛑 NPC状态自动更新已停止")
    async def _auto_update_loop(self):
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._update_npc_states()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ 自动更新失败: {e}")
                # 继续运行,不中断
    async def _update_npc_states(self):
        try:
            print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] 开始批量更新NPC对话...")
            new_dialogues = self.batch_generator.generate_batch_dialogues()
            self.current_dialogues = new_dialogues
            self.last_update = datetime.now()
            self.next_update_time = datetime.now()
            print("📝 NPC对话已更新:")
            for npc_name, dialogue in new_dialogues.items():
                print(f"   - {npc_name}: {dialogue}")
        except Exception as e:
            print(f"❌ 更新NPC状态失败: {e}")
    def get_current_state(self)->Dict:
        # 计算下次更新倒计时
        if self.last_update:
            elapsed = (datetime.now() - self.last_update).total_seconds()
            next_update_in = max(0, int(self.update_interval - elapsed))
        else:
            next_update_in = self.update_interval
        
        return {
            "dialogues": self.current_dialogues,
            "last_update": self.last_update,
            "next_update_in": next_update_in
        }
    def get_npc_dialogue(self, npc_name: str) -> Optional[str]:
        return self.current_dialogues.get(npc_name)
    async def force_update(self):
        print("⚡ 强制更新NPC状态...")
        await self._update_npc_states()
_state_manager = None
def get_state_manager(update_interval: int = 30) -> NPCStateManager:
    """获取状态管理器单例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = NPCStateManager(update_interval)
    return _state_manager