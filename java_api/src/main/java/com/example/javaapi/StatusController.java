package com.example.javaapi;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class StatusController {

    @GetMapping("/api/java/status")
    public Map<String, String> status() {
        return Map.of("service", "java-api", "status", "ok");
    }
}
