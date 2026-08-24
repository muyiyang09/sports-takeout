package com.sky.task;

import com.sky.entity.DispatchPool;
import com.sky.entity.Orders;
import com.sky.mapper.CoachScheduleMapper;
import com.sky.mapper.DispatchPoolMapper;
import com.sky.mapper.OrderMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;

@Component
@Slf4j
public class OrderTask {

    @Autowired
    private OrderMapper orderMapper;
    @Autowired
    private DispatchPoolMapper dispatchPoolMapper;
    @Autowired
    private CoachScheduleMapper coachScheduleMapper;

    /**
     * 派单池超时定时任务:每分钟扫描超时未派的派单池记录,取消订单并释放排期
     */
    @Scheduled(fixedRate = 60000)
    public void processDispatchTimeout() {
        log.info("定时处理派单池超时订单:{}", LocalDateTime.now());

        List<DispatchPool> expiredList = dispatchPoolMapper.listExpired(DispatchPool.STATUS_PENDING);
        if (expiredList == null || expiredList.isEmpty()) {
            return;
        }
        for (DispatchPool pool : expiredList) {
            try {
                // 1.取消派单池记录
                DispatchPool update = DispatchPool.builder()
                        .id(pool.getId())
                        .status(DispatchPool.STATUS_CANCELLED)
                        .build();
                dispatchPoolMapper.update(update);

                // 2.取消订单
                Orders orders = Orders.builder()
                        .id(pool.getOrderId())
                        .status(Orders.CANCELLED)
                        .cancelReason("派单超时")
                        .cancelTime(LocalDateTime.now())
                        .updateTime(LocalDateTime.now())
                        .build();
                orderMapper.update(orders);

                // 3.释放排期
                Orders ordersDB = orderMapper.getById(pool.getOrderId());
                if (ordersDB != null && ordersDB.getScheduleId() != null) {
                    coachScheduleMapper.releaseSchedule(ordersDB.getScheduleId(),
                            com.sky.entity.CoachSchedule.STATUS_AVAILABLE);
                }
            } catch (Exception e) {
                log.error("处理派单池超时失败,poolId={}", pool.getId(), e);
            }
        }
    }
}
