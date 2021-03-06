package com.dell.cpsd.paqx.dne.service.task.handler;

import com.dell.cpsd.paqx.dne.domain.Job;
import com.dell.cpsd.paqx.dne.service.model.Status;
import com.dell.cpsd.paqx.dne.service.model.TaskResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Created by madenb on 4/27/2017.
 */
public class BaseTaskHandler {
    private static final Logger LOGGER = LoggerFactory.getLogger(BaseTaskHandler.class);

    public TaskResponse initializeResponse(Job job){
        TaskResponse response = new TaskResponse();
        response.setWorkFlowTaskName(job.getCurrentTask().getTaskName());
        response.setWorkFlowTaskStatus(Status.IN_PROGRESS);
        job.addTaskResponse(job.getStep(), response);

        return response;
    }

    public boolean preExecute(Job job) {
        LOGGER.info("preExecute: " + job.getCurrentTask().getTaskName());
        return true;
    }

    public boolean postExecute(Job job) {
        LOGGER.info("postExecute: " + job.getCurrentTask().getTaskName());
        return true;
    }
}
