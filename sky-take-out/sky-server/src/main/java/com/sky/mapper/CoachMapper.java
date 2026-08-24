package com.sky.mapper;

import com.github.pagehelper.Page;
import com.sky.annotation.AutoFill;
import com.sky.dto.CoachPageQueryDTO;
import com.sky.entity.Coach;
import com.sky.enumeration.OperationType;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface CoachMapper {

    /**
     * 新增教练
     * @param coach
     */
    @AutoFill(value = OperationType.INSERT)
    void insert(Coach coach);

    /**
     * 更新教练(动态字段)
     * @param coach
     */
    @AutoFill(value = OperationType.UPDATE)
    void update(Coach coach);

    /**
     * 根据id查询教练
     * @param id
     * @return
     */
    @Select("select * from coach where id = #{id}")
    Coach getById(Long id);

    /**
     * 根据手机号查询教练
     * @param phone
     * @return
     */
    @Select("select * from coach where phone = #{phone}")
    Coach getByPhone(String phone);

    /**
     * 分页查询教练(管理端,按姓名/手机号/状态)
     * @param coachPageQueryDTO
     * @return
     */
    Page<Coach> pageQuery(CoachPageQueryDTO coachPageQueryDTO);

    /**
     * 按城市分页查询已审教练(用户端)
     * @param cityCode
     * @return
     */
    Page<Coach> listByCity(String cityCode);

}
