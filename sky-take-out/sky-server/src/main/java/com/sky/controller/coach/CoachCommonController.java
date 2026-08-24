package com.sky.controller.coach;

import com.sky.result.Result;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.util.UUID;

/**
 * 教练端通用接口（图片上传，本地存储）
 */
@RestController
@RequestMapping("/coach/common")
@Slf4j
@Api(tags = "教练端通用接口")
public class CoachCommonController {

    /**
     * 头像/图片上传，返回可访问的相对路径
     */
    @PostMapping("/upload")
    @ApiOperation("图片上传")
    public Result<String> upload(MultipartFile file) {
        try {
            String original = file.getOriginalFilename();
            String ext = original.substring(original.lastIndexOf("."));
            String name = UUID.randomUUID().toString().replace("-", "") + ext;
            File dir = new File("upload");
            if (!dir.exists()) {
                dir.mkdirs();
            }
            file.transferTo(new File(dir, name));
            return Result.success("/upload/" + name);
        } catch (Exception e) {
            log.error("图片上传失败：{}", e);
            return Result.error("上传失败");
        }
    }
}
