package com.sky.controller.admin;

import com.sky.result.Result;
import com.sky.service.DispatchPoolService;
import com.sky.vo.DispatchPoolVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 管理端派单池监控
 */
@RestController("adminDispatchPoolController")
@RequestMapping("/admin/dispatchPool")
@Api(tags = "管理端派单池监控接口")
@Slf4j
public class DispatchPoolController {

    @Autowired
    private DispatchPoolService dispatchPoolService;

    /**
     * 查询全部派单池记录（可按状态/城市筛选）
     */
    @GetMapping("/list")
    @ApiOperation("派单池监控列表")
    public Result<List<DispatchPoolVO>> list(
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String cityCode) {
        log.info("派单池监控查询：status={}, cityCode={}", status, cityCode);
        List<DispatchPoolVO> list = dispatchPoolService.listAllForAdmin(status, cityCode);
        return Result.success(list);
    }
}
