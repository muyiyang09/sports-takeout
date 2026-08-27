package com.sky.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Date;
import java.util.Map;

public class JwtUtil {
    /**
     * 生成jwt
     * 使用 HMAC-SHA 算法签名（HS256/HS384/HS512，由密钥长度决定）
     *
     * @param secretKey jwt秘钥
     * @param ttlMillis jwt过期时间(毫秒)
     * @param claims    设置的信息
     * @return
     */
    public static String createJWT(String secretKey, long ttlMillis, Map<String, Object> claims) {
        // 生成JWT的时间
        long expMillis = System.currentTimeMillis() + ttlMillis;
        Date exp = new Date(expMillis);

        // 设置jwt的body并签名
        return Jwts.builder()
                // 如果有私有声明，一定要先设置自己创建的私有声明，否则会覆盖标准声明
                .claims(claims)
                // 使用派生出的 HMAC 密钥签名
                .signWith(getSigningKey(secretKey))
                // 设置过期时间
                .expiration(exp)
                .compact();
    }

    /**
     * Token解密
     *
     * @param secretKey jwt秘钥 此秘钥一定要保留好在服务端, 不能暴露出去, 否则sign就可以被伪造, 如果对接多个客户端建议改造成多个
     * @param token     加密后的token
     * @return
     */
    public static Claims parseJWT(String secretKey, String token) {
        return Jwts.parser()
                // 校验签名使用的密钥
                .verifyWith(getSigningKey(secretKey))
                .build()
                // 解析并校验 token
                .parseSignedClaims(token)
                .getPayload();
    }

    /**
     * 由配置的字符串密钥派生出 HMAC 密钥。
     * jjwt 0.12 起要求 HMAC 密钥长度 >= 256 bit(32 字节)；当前配置密钥已为
     * 64 位随机串，无需处理。这里对 <32 字节的短密钥补零到 32 字节，仅作防御性兜底。
     */
    private static SecretKey getSigningKey(String secretKey) {
        byte[] bytes = secretKey.getBytes(StandardCharsets.UTF_8);
        if (bytes.length < 32) {
            bytes = Arrays.copyOf(bytes, 32);
        }
        return Keys.hmacShaKeyFor(bytes);
    }
}
