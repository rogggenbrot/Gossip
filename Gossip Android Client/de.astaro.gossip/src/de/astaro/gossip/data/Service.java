package de.astaro.gossip.data;

/*
 * Representation of a service containing database identifier, unique service
 * name, amount of watchers and amount of errors
 */
public class Service implements Comparable<Service>{
	private long id;
	private String name;
	private int watchers;
	private int errors;
	
	public long getId(){
		return id;
	}
	
	public void setId(long id){
		this.id = id;
	}
	
	public String getName(){
		return name;
	}
	
	public void setName(String name){
		this.name = name;
	}
	
	public void setAmountOfWatchers(int watchers){
		this.watchers = watchers;
	}
	
	public int getAmountOfWatchers(){
		return watchers;
	}
	
	public void setAmountOfErrors(int errors){
		this.errors = errors;
	}
	
	public int getAmountOfErrors(){
		return errors;
	}
	
	@Override 
	public String toString(){
		return name + " (" + (watchers-errors) + "/" + watchers + ") ";
	}
	
	public String toShortString(){
		String[] compName = name.split("/");
		String ret;
		
		if(compName[0].length() < 5){
			ret = compName[0] + "../" + compName[compName.length-1] +  " (" + 
								(watchers-errors) + "/" + watchers + ") ";
		}else{
			ret = compName[0].subSequence(0, 5) + "../" + compName[compName.length-1] +  
								" (" + (watchers-errors) + "/" + watchers + ") ";
		}
			
		return ret;
	}
	
	public int compareTo(Service another) {
		return name.compareTo(another.getName());
	}
}
