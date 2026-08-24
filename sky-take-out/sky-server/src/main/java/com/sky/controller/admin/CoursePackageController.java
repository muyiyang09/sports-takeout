package com.sky.controller.admin;

import com.sky.dto.CoursePackageDTO;
import com.sky.dto.CoursePackagePageQueryDTO;
import com.sky.result.PageResult;
import com.sky.result.Result;
import com.sky.service.CoursePackageService;
import com.sky.vo.CoursePackageVO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/admin/course_package")
@Api(tags = "训练套餐相关接口")
@Slf4j
public class CoursePackageController {

    @Autowired
    private CoursePackageService coursePackageService;

    /**
     * 新增套餐
     * @param coursePackageDTO
     * @return
     */
    @PostMapping
    @ApiOperation("新增套餐")
    @CacheEvict(cacheNames = "coursePackageCache", key = "#coursePackageDTO.categoryId")
    public Result save(@RequestBody CoursePackageDTO coursePackageDTO) {
        log.info("新增套餐：{}", coursePackageDTO);
        coursePackageService.save(coursePackageDTO);
        return Result.success();
    }

    /**
     * 分页查询
     * @param coursePackagePageQueryDTO
     * @return
     */
    @GetMapping("/page")
    @ApiOperation("分页查询")
    public Result<PageResult> page(CoursePackagePageQueryDTO coursePackagePageQueryDTO) {
        log.info("套餐分页查询：{}", coursePackagePageQueryDTO);
        PageResult pageResult = coursePackageService.pageQuery(coursePackagePageQueryDTO);
        return Result.success(pageResult);
    }

    /**
     * 批量删除套餐
     * @param ids
     * @return
     */
    @DeleteMapping
    @ApiOperation("批量删除套餐")
    @CacheEvict(cacheNames = "coursePackageCache", allEntries = true)
    public Result delete(@RequestParam List<Long> ids) {
        log.info("批量删除套餐：{}", ids);
        coursePackageService.deleteBatch(ids);
        return Result.success();
    }

    /**
     * 根据id查询套餐，用于修改页面回显数据
     *
     * @param id
     * @return
     */
    @GetMapping("/{id}")
    @ApiOperation("根据id查询套餐")
    public Result<CoursePackageVO> getById(@PathVariable Long id) {
        log.info("根据id查询套餐：{}", id);
        CoursePackageVO coursePackageVO = coursePackageService.getById(id);
        return Result.success(coursePackageVO);
    }

    /**
     * 修改套餐
     *
     * @param coursePackageDTO
     * @return
     */
    @PutMapping
    @ApiOperation("修改套餐")
    @CacheEvict(cacheNames = "coursePackageCache", allEntries = true)
    public Result update(@RequestBody CoursePackageDTO coursePackageDTO) {
        log.info("修改套餐：{}", coursePackageDTO);
        coursePackageService.update(coursePackageDTO);
        return Result.success();
    }

    /**
     * 套餐起售停售
     * @param status
     * @param id
     * @return
     */
    @PostMapping("/status/{status}")
    @ApiOperation("套餐起售停售")
    @CacheEvict(cacheNames = "coursePackageCache", allEntries = true)
    public Result startOrStop(@PathVariable Integer status, Long id) {
        log.info("套餐起售停售：{}", status);
        coursePackageService.startOrStop(status, id);
        return Result.success();
    }

    /**
     * 根据分类id查询套餐
     * @param categoryId
     * @return
     */
    @GetMapping("/list")
    @ApiOperation("根据分类id查询套餐")
    public Result<List<com.sky.entity.CoursePackage>> list(Long categoryId) {
        List<com.sky.entity.CoursePackage> list = coursePackageService.list(categoryId);
        return Result.success(list);
    }
}
