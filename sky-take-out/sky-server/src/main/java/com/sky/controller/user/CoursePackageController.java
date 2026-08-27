package com.sky.controller.user;

import com.sky.entity.Course;
import com.sky.entity.CoursePackage;
import com.sky.result.Result;
import com.sky.service.CoursePackageService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController("userCoursePackageController")
@RequestMapping("/user/course_package")
@Tag(name = "C端-训练套餐浏览接口")
@Slf4j
public class CoursePackageController {
    @Autowired
    private CoursePackageService coursePackageService;

    /**
     * 根据分类id查询套餐
     *
     * @param categoryId
     * @return
     */
    @GetMapping("/list")
    @Operation(summary = "根据分类id查询套餐")
    @Cacheable(cacheNames = "coursePackageCache", key = "#categoryId")
    public Result<List<CoursePackage>> list(Long categoryId) {
        List<CoursePackage> list = coursePackageService.list(categoryId);
        return Result.success(list);
    }

    /**
     * 根据套餐id查询包含的课程列表
     *
     * @param id
     * @return
     */
    @GetMapping("/course/{id}")
    @Operation(summary = "根据套餐id查询包含的课程列表")
    public Result<List<Course>> courseList(@PathVariable("id") Long id) {
        List<Course> list = coursePackageService.getCourseListByPackageId(id);
        return Result.success(list);
    }
}
