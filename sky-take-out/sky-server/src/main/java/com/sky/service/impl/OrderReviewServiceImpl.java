package com.sky.service.impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import com.sky.constant.MessageConstant;
import com.sky.context.BaseContext;
import com.sky.dto.OrderReviewDTO;
import com.sky.dto.OrderReviewPageQueryDTO;
import com.sky.entity.OrderDetail;
import com.sky.entity.OrderReview;
import com.sky.entity.Orders;
import com.sky.exception.OrderBusinessException;
import com.sky.mapper.OrderDetailMapper;
import com.sky.mapper.OrderMapper;
import com.sky.mapper.OrderReviewMapper;
import com.sky.result.PageResult;
import com.sky.service.OrderReviewService;
import com.sky.vo.OrderReviewVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class OrderReviewServiceImpl implements OrderReviewService {

    @Autowired
    private OrderReviewMapper orderReviewMapper;
    @Autowired
    private OrderMapper orderMapper;
    @Autowired
    private OrderDetailMapper orderDetailMapper;

    /**
     * 提交评价
     */
    @Override
    @Transactional
    public void submit(OrderReviewDTO orderReviewDTO) {
        Long orderId = orderReviewDTO.getOrderId();

        //1.校验订单存在且状态=已完成
        Orders order = orderMapper.getById(orderId);
        if (order == null) {
            throw new OrderBusinessException(MessageConstant.ORDER_NOT_FOUND);
        }
        if (!Orders.COMPLETED.equals(order.getStatus())) {
            throw new OrderBusinessException(MessageConstant.ORDER_STATUS_ERROR);
        }

        //2.校验未评价
        OrderReviewVO exist = orderReviewMapper.getByOrderId(orderId);
        if (exist != null) {
            throw new OrderBusinessException("该订单已评价");
        }

        //3.从订单明细取 coachId/courseId(订单本身 coachId 优先)
        Long coachId = order.getCoachId();
        Long courseId = null;
        List<OrderDetail> details = orderDetailMapper.getByOrderId(orderId);
        if (details != null && !details.isEmpty()) {
            OrderDetail first = details.get(0);
            if (coachId == null) {
                coachId = first.getCoachId();
            }
            courseId = first.getCourseId();
        }

        //4.插入评价
        OrderReview review = OrderReview.builder()
                .orderId(orderId)
                .userId(BaseContext.getCurrentId())
                .coachId(coachId)
                .courseId(courseId)
                .coachRating(orderReviewDTO.getCoachRating())
                .courseRating(orderReviewDTO.getCourseRating())
                .content(orderReviewDTO.getContent())
                .images(orderReviewDTO.getImages())
                .createTime(LocalDateTime.now())
                .build();
        orderReviewMapper.insert(review);

        //5.回填教练综合评分(教练评分均值)
        if (coachId != null) {
            orderReviewMapper.updateCoachRating(coachId);
        }
    }

    /**
     * 根据订单id查询评价
     */
    @Override
    public OrderReviewVO getByOrderId(Long orderId) {
        return orderReviewMapper.getByOrderId(orderId);
    }

    /**
     * 按教练分页查询评价
     */
    @Override
    public PageResult pageQueryByCoach(Long coachId, int page, int pageSize) {
        PageHelper.startPage(page, pageSize);
        OrderReviewPageQueryDTO dto = new OrderReviewPageQueryDTO();
        dto.setCoachId(coachId);
        Page<OrderReviewVO> p = orderReviewMapper.pageQueryByCoach(dto);
        return new PageResult(p.getTotal(), p.getResult());
    }
}
