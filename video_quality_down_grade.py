# coding: utf-8
"""
Subject: 视频质量分降级逻辑

WARNNING: 若对原始视频进行处理，存在兼容性问题:
13.0.8版本中对内容画像中的VideoDetails中的ori属性进行移除，
新增oriVideoDetail字段，但是13.0.7无该字段，
考虑兼容性13.0.7暂时获取VideoDetails中的ori属性
1. 对视频HEVC/AVC做优先级处理
2. 只对视频最高分辨率进行处理
"""
import os
import json
import logging
import traceback
logging.basicConfig(format='%(asctime)s|%(name)s|%(filename)s|%(funcName)s|%(levelname)s|%(lineno)d: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %p',
                    level=logging.INFO)


logger = logging.getLogger('run')


class videoQualityDownGrade:
    def __init__(self, config_path):
        self.contents = None
        self.priority_video_code = None
        self.priority_video_resolution = None
        self.select_video_source = None
        self.down_grade = None
        self.video_resolution_type = None
        self.key_venc = None
        self.key_quality = None
        self.key_resolution = None
        self.key_vbr = None
        self.key_ori = None
        self.contents = self.load_json(config_path)
        self.load_config(self.contents)
        
    def load_config(self, contents):
        """
        解析配置文件中的key
        :param contents: dict, 配置文件信息
        :return: None, 配置文件信息各字段
        """
        try:
            video_quality_config = contents["VideoQuaInfo"]["VideoQualityDownGradePriority"]
            self.down_grade = video_quality_config["DownGrade"]
            self.priority_video_code = video_quality_config["Priority"]["PriorityVideoCode"]
            self.priority_video_resolution = video_quality_config["Priority"]["PriorityVideoResolution"]
            self.select_video_source = video_quality_config["Priority"]["SelectVideoSource"]
            # 由于接入的信息存在不可控风险，所以key的名称做成可配置
            self.video_details_keyName = video_quality_config["VideoDetailsKeyName"]
            self.key_venc = self.video_details_keyName["venc"]
            self.key_resolution = self.video_details_keyName["resolution"]
            self.key_resolution_split = self.video_details_keyName["resolution_split"]
            self.key_quality = self.video_details_keyName["quality"]
            self.key_vbr = self.video_details_keyName["vbr"]
            self.key_ori = self.video_details_keyName["ori"]
            
        except Exception as _:
            self.video_details_keyName = None
            error_msg = traceback.format_exc()
            logger.error(error_msg)
        
        finally:
            pass
        
    @staticmethod
    def load_json(config_path):
        """
        读取配置文件
        :param config_path: str, 配置文件路径
        :return: dict, 配置文件信息
        """
        if not os.path.exists(config_path):
            return {}
        with open(config_path, 'r', encoding='utf-8') as fr:
            contents = json.load(fr)
        return contents
    
    def parse_video_resolution_type(self, resolution):
        """
        解析视频分辨率，获取对应分辨率类型
        :param resolution: str, 输入视频分辨率
        :return: str, 视频分辨率类型
        """
        
        resolution = list(map(lambda x: int(x), resolution.split(self.key_resolution_split)))
        for config_resolution_type_values in self.priority_video_resolution:
            config_resolution_type, config_resolution_values = config_resolution_type_values
            config_resolution_min_value = min(config_resolution_values)
            if min(resolution) >= config_resolution_min_value:
                return config_resolution_type
    
    def judge_video_vbr_status(self, real_video_vbr, config_video_vbr):
        """
        判断码率是否符合
        :param real_video_vbr: str, 视频真实码率
        :param config_video_vbr: str, 对应编码/分辨率/视频来源的要求码率
        :return: bool, True为符合，False为不符合
        """
        real_video_vbr = float(real_video_vbr)
        config_video_vbr = float(config_video_vbr)
        logger.info(f'real_video_vbr: {real_video_vbr} config_video_vbr: {config_video_vbr}')
        if config_video_vbr > 0 and real_video_vbr >= config_video_vbr:
            return True
        return False
    
    def judge_video_quality(self, video_quality, real_video_venc, real_resolution_type, detail, video_source_type):
        """
        判断对应视频编码类型/分辨率的码率是否符合
        :param video_quality: str, 视频处理前画质等级
        :param real_video_venc: str, 视频真实编码类型
        :param real_resolution_type: str, 视频真实分辨率类型
        :param detail: dict, 读取内容画像话单中的json串
        :param video_source_type: str, 运营要求对原始视频/编码后的视频进行处理
        :return: vbr_status, bool, True为符合，False为不符合
        :return: video_quality, str, 降级后的视频画质
        """
        real_video_vbr = detail[self.key_vbr]
        # 根据真实值获取配置文件中的vbr值
        config_video_vbr = self.down_grade[real_video_venc][real_resolution_type][video_source_type][self.key_vbr]
        vbr_status = self.judge_video_vbr_status(real_video_vbr, config_video_vbr)
        if not vbr_status:
            down_grade_video_quality = self.down_grade[real_video_venc][real_resolution_type][video_source_type]["videoQuality"]
            video_quality = down_grade_video_quality

        return vbr_status, video_quality
        
    def process_ori_video_type(self, video_quality, video_details, ori_video_detail, video_source_type):
        '''
        对原始视频进行质量分降级逻辑
        :param video_quality: str, 视频处理前画质等级
        :param video_details: list(dict), 读取内容画像话单中VideoDetails字段的json串
        :param ori_video_detail: list(dict), 读取内容画像话单中orivideoDetail字段的json串
        :param video_source_type: str, 运营要求对原始视频/编码后的视频进行处理
        :return: video_quality, str, 降级后的视频画质
        '''
        has_ori_venc = False
        vbr_status = True
        for detail in video_details:
            # 若videoDetails字段中有ori属性，就用
            if detail[self.key_quality] == self.key_ori:
                has_ori_venc = True
                logger.info(f'using VideoDetails ori, detail: {detail}')
                real_video_venc = detail[self.key_venc]
                real_video_resolution = detail[self.key_resolution]
                real_resolution_type = self.parse_video_resolution_type(real_video_resolution)
                vbr_status, new_video_quality = self.judge_video_quality(video_quality, real_video_venc, real_resolution_type, detail, video_source_type)    
                if not vbr_status:
                    logger.info(f"""real_video_venc: {real_video_venc},
                                    real_video_resolution: {real_video_resolution},
                                    vbr_status results: {vbr_status},
                                    original video_quality: {video_quality},
                                    new video_quality: {new_video_quality}""")
                    video_quality = new_video_quality
                    break
        
        # 若videoDetails字段中没有ori属性，就从ori_video_detail中获取
        if not has_ori_venc:
            logger.info(f'using oriVideoDetail ori, detail: {ori_video_detail}')
            real_video_venc = ori_video_detail[self.key_venc]
            real_video_resolution = ori_video_detail[self.key_resolution]
            real_resolution_type = self.parse_video_resolution_type(real_video_resolution)
            vbr_status, new_video_quality = self.judge_video_quality(video_quality, real_video_venc, real_resolution_type, detail, video_source_type)    
            if not vbr_status:
                logger.info(f"""real_video_venc: {real_video_venc},
                                    real_video_resolution: {real_video_resolution},
                                    vbr_status results: {vbr_status},
                                    original video_quality: {video_quality},
                                    new video_quality: {new_video_quality}""")
                video_quality = new_video_quality
                
        if vbr_status:
            logger.info(f'keep original videoQuality: {video_quality}')
        return video_quality
                    
    def process_transcode_video_type(self, video_quality, video_details, video_source_type):
        '''
        对转码后的视频进行质量分降级逻辑
        :param video_quality: str, 视频处理前画质等级
        :param video_details: list(dict), 读取内容画像话单中VideoDetails字段的json串
        :param video_source_type: str, 运营要求对原始视频/编码后的视频进行处理
        :return: video_quality, str, 降级后的视频画质
        '''
        # 遍历VideoDetails内容, 不受接入侧的排序规则限制
        vbr_status = True
        for config_priority_venc in self.priority_video_code:
            for config_resoluion_type_values in self.priority_video_resolution:
                config_resoluion_type, _ = config_resoluion_type_values
                for detail in video_details:
                    real_video_venc = detail[self.key_venc]
                    real_video_quality = detail[self.key_quality]
                    real_video_resolution = detail[self.key_resolution]
                    real_resolution_type = self.parse_video_resolution_type(real_video_resolution)
                    flag_video_real_quality = (real_video_quality != self.key_ori)
                    flag_video_real_venc = (real_video_venc == config_priority_venc)
                    flag_video_real_resoluion_type = (config_resoluion_type == real_resolution_type)
                    # 若为转码视频类型&视频编码格式命中&视频分辨率类型命中: 不管vbr校验结果如何，都返回
                    if flag_video_real_quality and flag_video_real_venc and flag_video_real_resoluion_type:
                        logger.info(f'enter judge_video_quality, detail: {detail}')
                        vbr_status, new_video_quality = self.judge_video_quality(video_quality, real_video_venc, real_resolution_type, detail, video_source_type)
                        if not vbr_status:
                            logger.info(f"""real_video_venc: {real_video_venc},
                                    real_video_resolution: {real_video_resolution},
                                    vbr_status results: {vbr_status},
                                    original video_quality: {video_quality},
                                    new video_quality: {new_video_quality}""")
                            video_quality = new_video_quality
                        return video_quality
        if vbr_status:
            logger.info(f'keep original videoQuality: {video_quality}')
        return video_quality 
    
    def process_high_video_quality(self, video_quality, video_details, ori_video_detail):
        '''
        对视频进行质量分降级逻辑
        :param video_quality: str, 视频处理前画质等级
        :param video_details: list(dict), 读取内容画像话单中VideoDetails字段的json串
        :param ori_video_detail: list(dict), 读取内容画像话单中orivideoDetail字段的json串
        :return: video_quality, str, 降级后的视频画质
        '''
        try:
            if video_quality != 'H':
                logger.info(f'not process video_quality')
                return video_quality
            video_source_type = self.select_video_source
            if video_source_type == 'VideoDetails':
                logger.info(f'video_source_type: {video_source_type}, see process_transcode_video_type function')
                video_quality = self.process_transcode_video_type(video_quality, video_details, video_source_type)
            else:
                logger.info(f'video_source_type: {video_source_type}, see process_ori_video_type function')
                video_quality = self.process_ori_video_type(video_quality, video_details, ori_video_detail, video_source_type)
                
            return video_quality
        
        except Exception as _:
            error_msg = traceback.format_exc()
            logger.error(error_msg)
            return video_quality
        
        finally:
            pass
            

if __name__ == '__main__':
    config_path = 'shortvideostreaming_config.json'
    test_video_quality = 'H'
    test_video_details_path = './test_case/videoDetails.json'
    test_ori_video_details_path = './test_case/oriVideoDetail.json'
    video_details = videoQualityDownGrade.load_json(test_video_details_path)
    ori_video_details = videoQualityDownGrade.load_json(test_ori_video_details_path)
    sol = videoQualityDownGrade(config_path)
    res = sol.process_high_video_quality(test_video_quality, video_details, ori_video_details)
    logger.info(f'inputs video_quality {test_video_quality}, return video_quality: {res}')