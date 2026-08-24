package com.sky.controller.coach;

import com.sky.dto.ServiceCompleteDTO;
import com.sky.result.PageResult;
import com.sky.result.Result;
import com.sky.service.DispatchPoolService;
import com.sky.service.OrderService;
import com.sky.vo.DispatchPoolVO;
import com.sky.vo.OrderVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 教练端订单接口:接单/拒单/开始服务/完成服务/抢单/接单列表/派单池可抢列表
 */
@RestController("coachOrderController")
@RequestMapping("/coach/order")
@Api(tags = "教练端订单相关接口")
@Slf4j
public class OrderController {

    @Autowired
    private OrderService orderService;
    @Autowired
    private DispatchPoolService dispatchPoolService;

    /**
     * 教练接单列表分页查询
     */
    @GetMapping("/list")
    @ApiOperation("教练接单列表分页查询")
    public Result<PageResult> list(int page, int pageSize, Integer status, Long coachId) {
        PageResult pageResult = orderService.pageQuery4Coach(page, pageSize, status, coachId);
        return Result.success(pageResult);
    }

    /**
     * 教练确认接单(指定单)
     */
    @PutMapping("/confirm")
    @ApiOperation("教练确认接单(指定单)")
    public Result confirm(Long id, Long coachId) {
        orderService.confirmOrder(id, coachId);
        return Result.success();
    }

    /**
     * 教练拒单(指定单)
     */
    @PutMapping("/reject")
    @ApiOperation("教练拒单(指定单)")
    public Result reject(Long id, Long coachId, String reason) {
        orderService.rejectOrder(id, coachId, reason);
        return Result.success();
    }

    /**
     * 派单池抢单
     */
    @PostMapping("/seize")
    @ApiOperation("派单池抢单")
    public Result seize(Long poolId, Long coachId) {
        orderService.seize(poolId, coachId);
        return Result.success();
    }

    /**
     * 开始服务
     */
    @PutMapping("/startService")
    @ApiOperation("开始服务")
    public Result startService(Long id, Long coachId) {
        orderService.startService(id, coachId);
        return Result.success();
    }

    /**
     * 完成服务(提交训练记录/体测数据)
     */
    @PutMapping("/completeService")
    @ApiOperation("完成服务")
    public Result completeService(@RequestBody ServiceCompleteDTO serviceCompleteDTO) {
        orderService.completeService(serviceCompleteDTO);
        return Result.success();
    }

    /**
     * 派单池可抢列表(按教练服务城市)
     */
    @GetMapping("/dispatchPool")
    @ApiOperation("派单池可抢列表")
    public Result<List<DispatchPoolVO>> dispatchPool(String cityCode) {
        List<DispatchPoolVO> list = dispatchPoolService.listSeizable(cityCode);
        return Result.success(list);
    }

    /**
     * 查询订单详情
     */
    @GetMapping("/details/{id}")
    @ApiOperation("查询订单详情")
    public Result<OrderVO> details(@PathVariable("id") Long id) {
        OrderVO orderVO = orderService.details(id);
        return Result.success(orderVO);
    }
}
