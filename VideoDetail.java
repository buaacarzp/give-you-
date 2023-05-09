import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class VideoDetail {

    private String venc;

    private String quality;

    private String resolution;


    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        VideoDetail that = (VideoDetail) o;
        return Objects.equals(venc, that.venc) && Objects.equals(quality, that.quality) && Objects.equals(resolution,
            that.resolution);
    }

    @Override
    public int hashCode() {
        return Objects.hash(venc, quality, resolution);
    }

    public static void main(String[] args) {
        // 读取配置，得到配置的VideoConfig优先级列表
        List<VideoDetail> detailConfigPriorities = new ArrayList<>();

        // 读取json，得到输入的VideoConfig列表
        List<VideoDetail> inputDetails = new ArrayList<>();

        for (VideoDetail detailConfig: detailConfigPriorities){
            int index = inputDetails.indexOf(detailConfig);
            VideoDetail detail = inputDetails.get(index);
        }

    }
}


