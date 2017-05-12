/**
 * Copyright &copy; 2017 Dell Inc. or its subsidiaries.  All Rights Reserved.
 * Dell EMC Confidential/Proprietary Information
 */
package com.dell.cpsd.paqx.dne.amqp.config;

import com.dell.cpsd.common.rabbitmq.config.RabbitMQPropertiesConfig;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;
import org.springframework.context.annotation.PropertySources;

/**
 * The configuration for the client.
 * <p>
 * Copyright &copy; 2017 Dell Inc. or its subsidiaries.  All Rights Reserved.
 * Dell EMC Confidential/Proprietary Information
 * </p>
 */
@Configuration
@PropertySources({@PropertySource(value = "classpath:META-INF/spring/dne-paqx/rabbitmq.properties"),
        @PropertySource(value = "file:/opt/dell/cpsd/dne-paqx/common/rabbitmq-config.properties", ignoreResourceNotFound = true)})
@Qualifier("rabbitPropertiesConfig")
public class PropertiesConfig extends RabbitMQPropertiesConfig {

}

