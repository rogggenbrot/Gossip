package de.astaro.gossip.data;

import java.util.List;

import de.astaro.gossip.R;
import android.content.Context;
import android.graphics.Color;
import android.preference.PreferenceManager;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.app.Activity;

/*
 * Helper class to process a list of service objects in order to be displayed
 * by a ListActivity.
 */
public class ServiceAdapter extends ArrayAdapter<de.astaro.gossip.data.Service>{

    private Context context; 
    private int layoutResourceId;    
    private List<Service> data = null;
    
    /*
     * Initialize helper class.
     */
    public ServiceAdapter(Context context, int layoutResourceId, List<Service> data) {
        super(context, layoutResourceId, data);
        this.layoutResourceId = layoutResourceId;
        this.context = context;
        this.data = data;
    }

    /*
     * Process a single row of the list. Set the content to display and change backgroundcolor
     * according to the amount of errors and watchers of the service displayed by this row.
     * 
     * @see android.widget.ArrayAdapter#getView(int, android.view.View, android.view.ViewGroup)
     */
    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        View row = convertView;
        ServiceHolder holder = null;
        
        if(row == null)
        {
            LayoutInflater inflater = ((Activity)context).getLayoutInflater();
            row = inflater.inflate(layoutResourceId, parent, false);
            
            holder = new ServiceHolder();
            holder.txtTitle = (TextView)row.findViewById(R.id.txtTitle);
            
            row.setTag(holder);
        }
        else
        {
            holder = (ServiceHolder)row.getTag();
        }
        
        Service service = data.get(position);
        
        if(PreferenceManager.getDefaultSharedPreferences(context).getBoolean("full_service_name", false)){
        	holder.txtTitle.setText(service.toString());
        }else{
        	holder.txtTitle.setText(service.toShortString());
        }
        
        
        
        if(service.getAmountOfErrors() == 0){
        	row.setBackgroundColor(Color.rgb(133, 165, 98 ));
        }else if(service.getAmountOfErrors()/service.getAmountOfWatchers() > 0.5){
        	row.setBackgroundColor(Color.rgb(204, 92, 84 ));
        }else{
        	row.setBackgroundColor(Color.rgb(255, 255, 205 ));
        }
        
        
        return row;
    }
    
    /*
     * Wrapper class for a service row, may be expended.
     */
    static class ServiceHolder
    {
        TextView txtTitle;
    }
}