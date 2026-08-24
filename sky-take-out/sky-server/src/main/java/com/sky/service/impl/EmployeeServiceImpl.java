package com.sky.service.impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import com.sky.constant.MessageConstant;
import com.sky.constant.PasswordConstant;
import com.sky.constant.StatusConstant;
import com.sky.context.BaseContext;
import com.sky.dto.EmployeeDTO;
import com.sky.dto.EmployeeLoginDTO;
import com.sky.dto.EmployeePageQueryDTO;
import com.sky.dto.PasswordEditDTO;
import com.sky.entity.Employee;
import com.sky.exception.AccountLockedException;
import com.sky.exception.AccountNotFoundException;
import com.sky.exception.PasswordEditFailedException;
import com.sky.exception.PasswordErrorException;
import com.sky.mapper.EmployeeMapper;
import com.sky.result.PageResult;
import com.sky.service.EmployeeService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.DigestUtils;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class EmployeeServiceImpl implements EmployeeService {

    @Autowired
    private EmployeeMapper employeeMapper;

    /**
     * 员工登录
     *
     * @param employeeLoginDTO
     * @return
     */
    public Employee login(EmployeeLoginDTO employeeLoginDTO) {
        String username = employeeLoginDTO.getUsername();
        String password = employeeLoginDTO.getPassword();

        //1、根据用户名查询数据库中的数据
        Employee employee = employeeMapper.getByUsername(username);

        //2、处理各种异常情况（用户名不存在、密码不对、账号被锁定）
        if (employee == null) {
            //账号不存在
            throw new AccountNotFoundException(MessageConstant.ACCOUNT_NOT_FOUND);
        }

        //密码比对
        // TODO 后期需要进行md5加密，然后再进行比对

        password = DigestUtils.md5DigestAsHex(password.getBytes());
        if (!password.equals(employee.getPassword())) {
            //密码错误
            throw new PasswordErrorException(MessageConstant.PASSWORD_ERROR);
        }

        if (employee.getStatus() == StatusConstant.DISABLE) {
            //账号被锁定
            throw new AccountLockedException(MessageConstant.ACCOUNT_LOCKED);
        }

        //3、返回实体对象
        return employee;
    }

    @Override
    public void save(EmployeeDTO employeeDTO) {
        // TODO 保存员工信息
        Employee employee = new Employee();
        BeanUtils.copyProperties(employeeDTO, employee);  //   把dto对象中的属性复制到实体对象中
        employee.setStatus(StatusConstant.ENABLE);   //   设置默认状态为启用
        employee.setPassword(DigestUtils.md5DigestAsHex(PasswordConstant.DEFAULT_PASSWORD.getBytes())); //   设置默认密码
        //公共属性不需要设置,aop 会自动填充
//        employee.setUpdateTime(LocalDateTime.now());
//        employee.setCreateTime(LocalDateTime.now());
//
//        employee.setCreateUser(BaseContext.getCurrentId());  //  获取当前登录用户id
//        employee.setUpdateUser(BaseContext.getCurrentId());  //  获取当前登录用户id

        employeeMapper.insert(employee);     //   插入员工信息
    }

    @Override
    public PageResult pageQuery(EmployeePageQueryDTO employeePageQueryDTO) {
        // TODO 查询员工信息
        PageHelper.startPage(employeePageQueryDTO.getPage(), employeePageQueryDTO.getPageSize());//  开始分页 查询
        Page<Employee> page = employeeMapper.pageQuery(employeePageQueryDTO);

        long total = page.getTotal();
        List<Employee> records = page.getResult();
        return new PageResult(total, records);
    }

    /**
     * 启用或禁用员工
     * @param status
     * @param id
     */
    @Override
    public void startOrStop(Integer status, Long id) {
        // update employee set status = #{status} where id = #{id}
//        Employee employee = new Employee();
        Employee employee = Employee.builder().status(status).id(id).build();
        employeeMapper.update(employee);


    }

    @Override
    public Employee getById(Long id) {
        Employee employee = employeeMapper.selectByPrimaryKey(id);
        employee.setPassword("****");  //   密码不返回
        return employee;
    }

    @Override
    public void update(EmployeeDTO employeeDTO) {
        Employee employee = new Employee();
        BeanUtils.copyProperties(employeeDTO, employee);

//        employee.setUpdateTime(LocalDateTime.now());
//        employee.setUpdateUser(BaseContext.getCurrentId()); //  获取当前登录用户id
        employeeMapper.update(employee);
    }

    @Override
    public void editPassword(PasswordEditDTO passwordEditDTO) {
        // TODO 修改密码
        // 1.新旧密码重复抛出异常
        if(passwordEditDTO.getNewPassword().equals(passwordEditDTO.getOldPassword())){
            throw new PasswordEditFailedException(MessageConstant.PASSWORD_REPEAT);
        }
        // H获取当前用户的id
        Long empId = BaseContext.getCurrentId();
        // 2.获取用户输入加密后的新旧密码
        String oldPassword = DigestUtils.md5DigestAsHex(passwordEditDTO.getOldPassword().getBytes());
        String newPassword = DigestUtils.md5DigestAsHex(passwordEditDTO.getNewPassword().getBytes());
        // 封装对象
        passwordEditDTO.setNewPassword(newPassword);
        passwordEditDTO.setOldPassword(oldPassword);
        passwordEditDTO.setEmpId(empId);
        // 3.根据id查询原始密码
        Employee employee = employeeMapper.selectByPrimaryKey(empId);
        // 4.判断原始密码是否正确
        if (!employee.getPassword().equals(oldPassword)) {
            throw new PasswordErrorException(MessageConstant.OLDPASSWORD_ERROR);
        }
        // 5.密码格式正确，修改数据库中密码
        employeeMapper.updatePassword(passwordEditDTO);
    }

}
